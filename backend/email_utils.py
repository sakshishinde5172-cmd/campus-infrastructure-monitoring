import os
import smtplib
import threading
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


def _send(to_addr, subject, body):
    if not (SENDER and APP_PASSWORD and to_addr):
        return
    msg = EmailMessage()
    msg["From"] = f"CIMS Campus Support <{SENDER}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SENDER, APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"[email] failed to send to {to_addr}: {e}")


def send_status_email(to_addr, username, complaint_id, title, new_status):
    subject = f"Your complaint #{complaint_id} is now {new_status}"
    body = (
        f"Hi {username},\n\n"
        f"The status of your complaint \"{title}\" (#{complaint_id}) "
        f"has been updated to: {new_status}.\n\n"
        f"Thank you for helping keep our campus in good shape.\n"
        f"- CIMS Team"
    )
    threading.Thread(target=_send, args=(to_addr, subject, body), daemon=True).start()


def send_admin_new_complaint(complaint_id, title, location, username):
    subject = f"New complaint #{complaint_id}: {title}"
    body = (
        f"A new complaint was submitted by {username}.\n\n"
        f"Title: {title}\n"
        f"Location: {location}\n"
        f"ID: #{complaint_id}\n\n"
        f"Log in to the admin panel to review it."
    )
    threading.Thread(target=_send, args=(ADMIN_EMAIL, subject, body), daemon=True).start()