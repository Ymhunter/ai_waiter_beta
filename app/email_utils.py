import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

# Load environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # 👈 must be verified in SendGrid (Single Sender)
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL", SENDER_EMAIL)  # default same as sender


def send_email(to_email: str, subject: str, html_content: str):
    """
    Send an email using SendGrid.

    Args:
        to_email (str): recipient email address
        subject (str): subject of the email
        html_content (str): HTML content of the email
    """
    if not SENDGRID_API_KEY:
        raise RuntimeError("Missing SENDGRID_API_KEY in environment")
    if not SENDER_EMAIL:
        raise RuntimeError("Missing SENDER_EMAIL in environment")

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    # 👇 Add Reply-To header
    message.reply_to = Email(REPLY_TO_EMAIL)

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email}, status {response.status_code}")
        return response
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return None
