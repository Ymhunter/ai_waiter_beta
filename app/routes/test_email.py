from fastapi import APIRouter
from ..email_utils import send_email

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/email")
async def test_email():
    subject = "📧 Test Email from Barbershop Booking"
    html = """
    <h2>✅ Test Successful!</h2>
    <p>This is a test email sent via SendGrid from your FastAPI app.</p>
    <p>If you received this, your email setup works correctly 🎉</p>
    """

    # ⚠️ Replace with your verified email in SendGrid
    to_email = "your_verified_email@example.com"

    response = send_email(to_email, subject, html)

    if response:
        return {"status": "sent", "to": to_email}
    return {"status": "failed", "error": "Could not send email"}
