from email.message import EmailMessage
from email.utils import make_msgid
import ssl
import smtplib
import os
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def validate_env():
    missing = [k for k, v in {
        "EMAIL_SENDER": EMAIL_SENDER,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "EMAIL_RECEIVER": EMAIL_RECEIVER,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

def send_basic_email(subject: str, body: str, to: str | None = None):
    validate_env()
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to or EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.set_content(body)

    # Insecure: disabling SSL verification as requested. Do NOT use in production.
    context = ssl._create_unverified_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=30) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("[SUCCESS] Email sent to", msg["To"]) 

def send_email_with_image(
    subject: str,
    body_text: str,
    image_path: str,
    to: str | None = None,
    inline: bool = True,
):
    """Send an email with an image either inline (embedded) or as an attachment.

    Parameters:
      subject: Email subject line
      body_text: Plain text body
      image_path: Path to the image file
      to: Optional override recipient email address
      inline: If True, embed image in HTML body; else attach normally

    Note: SSL verification is disabled (insecure) per your earlier request.
    """
    validate_env()
    recipient = to or EMAIL_RECEIVER
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text)

    img_file = Path(image_path)
    if not img_file.exists():
        print(f"[WARN] Image not found at {image_path}; sending without image.")
    else:
        mime_type, _ = mimetypes.guess_type(img_file.name)
        if not mime_type:
            mime_type = "application/octet-stream"
        maintype, subtype = mime_type.split('/', 1)
        data = img_file.read_bytes()

        if inline:
            cid = make_msgid(domain="inline.image")[1:-1]  # strip <>
            html = f"""
            <html><body style='font-family:Arial,Helvetica,sans-serif;'>
              <p>{body_text}</p>
              <img src=\"cid:{cid}\" alt=\"Embedded Image\" style=\"max-width:600px;border:1px solid #ccc;padding:4px;\" />
            </body></html>
            """
            msg.add_alternative(html, subtype='html')
            # Attach related image to the HTML part
            for part in msg.iter_parts():
                if part.get_content_type() == 'text/html':
                    part.add_related(data, maintype=maintype, subtype=subtype, cid=f"<{cid}>", filename=img_file.name)
                    break
        else:
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=img_file.name)

    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=30) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("[SUCCESS] Email with image sent to", recipient, f"(inline={inline})")

if __name__ == "__main__":
    # Example basic email
    send_basic_email("From Python Server", "This is a test email sent from Python server.")

    # Example inline image email (update image filename if needed)
    send_email_with_image(
        subject="Inline Image Test",
        body_text="Here is an inline image.",
        image_path="birthday_card_custom.png",
        inline=True,
    )