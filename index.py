from email.message import EmailMessage
import ssl
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

emailPassword = os.getenv("EMAIL_PASSWORD")
emailSender = "jay.sanjay.karia@gmail.com"
emailReceiver = "jay.s.karia@gmail.com"

subject = "From Python Server"
body = "This is a test email sent from Python server."

em = EmailMessage()
em["From"] = emailSender
em["To"] = emailReceiver
em["Subject"] = subject
em.set_content(body)

# Currently Bypasses the SSL certificate verification
context = ssl._create_unverified_context()

# Log in and send the email
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(emailSender, emailPassword)
    smtp.sendmail(emailSender, emailReceiver, em.as_string())