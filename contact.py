import smtplib
from email.message import EmailMessage
import os

# Microsoft 365 SMTP settings
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
USERNAME = os.environ.get("EMAIL_USER")
PASSWORD = os.environ.get("EMAIL_PASS")

def send_email(name, email, message):
    """
    Send an email via Microsoft 365 using the contact form data.
    """
    msg = EmailMessage()
    msg['Subject'] = f'New message from {name}'
    msg['From'] = USERNAME
    msg['To'] = USERNAME
    msg.set_content(f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}")

    # Connect to SMTP server, start TLS, login, and send the message
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(USERNAME, PASSWORD)
        smtp.send_message(msg)