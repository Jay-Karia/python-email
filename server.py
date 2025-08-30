"""FastAPI server to receive an uploaded image and email it.

Endpoints:
  GET /health               -> Health check
  POST /send-email          -> Send an email with uploaded image

POST /send-email (multipart/form-data fields):
  subject:   (str)   required
  body:      (str)   required (plain text body)
  inline:    (bool)  optional (default true) embed image inline; if false attaches
  to:        (str)   optional override default receiver
  image:     (file)  required image file to embed/attach

Environment variables (from .env):
  EMAIL_SENDER
  EMAIL_PASSWORD (Gmail App Password if using Gmail + 2FA)
  EMAIL_RECEIVER (default recipient)

Run locally:
  uvicorn server:app --reload --port 8000

Then test with curl (PowerShell quoting rules) or a tool like Postman.
"""
from __future__ import annotations

import os
import ssl
import mimetypes
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import smtplib

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

app = FastAPI(title="Email Image Sender", version="1.0.0")


def validate_env() -> None:
    missing = [k for k, v in {
        "EMAIL_SENDER": EMAIL_SENDER,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "EMAIL_RECEIVER": EMAIL_RECEIVER,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def build_email(subject: str, plain_text: str, html_body: Optional[str] = None, to_addr: Optional[str] = None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_addr or EMAIL_RECEIVER
    msg["Subject"] = subject
    if html_body:
        msg.set_content(plain_text)
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(plain_text)
    return msg


def attach_image(msg: EmailMessage, filename: str, data: bytes, inline: bool) -> Optional[str]:
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"
    maintype, subtype = mime_type.split('/', 1)

    if inline:
        cid = make_msgid(domain="inline.image")[1:-1]  # strip <>
        msg.add_related(data, maintype=maintype, subtype=subtype, cid=f"<{cid}>", filename=filename)
        return cid
    else:
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
        return None


def send_email(msg: EmailMessage) -> None:
    # Insecure: disabling SSL verification as requested. Do NOT use in production.
    context = ssl._create_unverified_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="SMTP authentication failed. Check credentials / app password.")
    except ssl.SSLError as e:
        raise HTTPException(status_code=525, detail=f"SSL error: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Unexpected error sending email: {e}")


@app.get("/health")
async def health():  # pragma: no cover - trivial
    try:
        validate_env()
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.post("/send-email")
async def send_email_endpoint(
    subject: str = Form(...),
    body: str = Form(...),
    inline: bool = Form(True),
    to: Optional[str] = Form(None),
    image: UploadFile = File(...),
):
    validate_env()

    # Basic filename sanitation (strip path components)
    filename = Path(image.filename).name
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    if inline:
        placeholder_cid = "cid_placeholder"
        html_body = f"""
        <html><body style='font-family:Arial,Helvetica,sans-serif'>
            <p>{body}</p>
            <img src="cid:{placeholder_cid}" alt="Image" style="max-width:600px;border:1px solid #ccc;padding:4px"/>
            <hr/><small>Sent automatically by Python server.</small>
        </body></html>
        """
        msg = build_email(subject, body, html_body, to)
        real_cid = attach_image(msg, filename, data, inline=True)
        # Replace placeholder in the HTML part
        for part in msg.iter_parts():
            if part.get_content_type() == "text/html":
                html = part.get_content().replace(placeholder_cid, real_cid)
                part.set_content(html, subtype="html")
    else:
        msg = build_email(subject, body, None, to)
        attach_image(msg, filename, data, inline=False)

    send_email(msg)
    return {"status": "sent", "to": msg["To"], "inline": inline, "filename": filename}


if __name__ == "__main__":  # Manual run helper
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
