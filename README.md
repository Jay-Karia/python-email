# Python Email Image Sender

This project provides:

1. A script (`index.py`) showing basic email send.
2. A FastAPI server (`server.py`) that accepts an uploaded image and emails it inline or as an attachment.

## Setup

1. Python 3.11+ recommended.
2. Create virtual environment (optional but recommended).
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECEIVER=default_receiver@gmail.com
```

Use a Gmail App Password (Google Account -> Security -> App passwords) if 2FA is enabled.

## Running the API Server

```powershell
python .\server.py
# or
uvicorn server:app --reload --port 8000
```

Visit: http://127.0.0.1:8000/docs for interactive Swagger UI.

## Endpoint Details

POST /send-email (multipart/form-data):
- subject (str) required
- body (str) required
- inline (bool) optional (default true). If true, embeds image in HTML body; if false, attaches it.
- to (str) optional override recipient
- image (file) required uploaded file

Example (PowerShell):

```powershell
$Form = @{
  subject = 'Test Subject'
  body = 'Hello from FastAPI inline email'
  inline = 'true'
}
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/send-email' -Method Post -Form $Form -InFile .\birthday_card_custom.png -ContentType 'multipart/form-data'
```

(For complex multipart including a file with PowerShell, it's often easier to use `curl` from Windows 10+ or a REST client.)

`curl` example (Git Bash / WSL / Windows curl):

```bash
curl -X POST http://127.0.0.1:8000/send-email \
  -F subject='Test Email' \
  -F body='Inline body test' \
  -F inline=true \
  -F image=@birthday_card_custom.png
```

## Sending Without the Server

Edit values in `index.py` and run:

```powershell
python .\index.py
```

## Troubleshooting

- SSL errors: run Python's `Install Certificates` script or `pip install --upgrade certifi`.
- Auth errors: ensure App Password is correct and not expired.
- Empty email variables: confirm `.env` is in project root and not named `.env.txt`.

## Future Enhancements

- Multiple attachments
- CC / BCC support
- OAuth2 (XOAUTH2) login for Gmail
- Rate limiting / auth for API
