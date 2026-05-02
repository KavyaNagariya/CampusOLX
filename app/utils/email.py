import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

NEW_RESERVATION_REQUEST_HTML = """
<html>
<body>
    <h2>New Reservation Request</h2>
    <p>Hello {seller_name},</p>
    <p>You have received a new reservation request for your item: <strong>{item_name}</strong>.</p>
    <p><strong>Buyer Details:</strong></p>
    <ul>
        <li>Username: {buyer_name}</li>
        <li>User ID: {buyer_id}</li>
        <li>Time: {request_time}</li>
    </ul>
    <p>Please log in to the app to accept or reject this request.</p>
    <br>
    <p>Best regards,</p>
    <p>Campus Marketplace Team</p>
</body>
</html>
"""

RESERVATION_ACCEPTED_HTML = """
<html>
<body>
    <h2>Reservation Request Accepted!</h2>
    <p>Hello {buyer_name},</p>
    <p>Great news! Your reservation request for <strong>{item_name}</strong> has been accepted by {seller_name}.</p>
    <p><strong>What's Next?</strong></p>
    <p>You can now view the seller's contact details in the app to finalize your purchase.</p>
    <br>
    <p>Best regards,</p>
    <p>Campus Marketplace Team</p>
</body>
</html>
"""

def send_email(to_email: str, subject: str, html_content: str):
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.EMAILS_FROM_EMAIL]):
        logger.warning("SMTP settings not configured. Skipping email.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = to_email

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, message.as_string())
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")

def send_new_reservation_email(seller_email: str, seller_name: str, item_name: str, buyer_name: str, buyer_id: int, request_time: str):
    subject = f"New Reservation Request for {item_name}"
    html = NEW_RESERVATION_REQUEST_HTML.format(
        seller_name=seller_name,
        item_name=item_name,
        buyer_name=buyer_name,
        buyer_id=buyer_id,
        request_time=request_time
    )
    send_email(seller_email, subject, html)

def send_reservation_accepted_email(buyer_email: str, buyer_name: str, item_name: str, seller_name: str):
    subject = f"Reservation Accepted: {item_name}"
    html = RESERVATION_ACCEPTED_HTML.format(
        buyer_name=buyer_name,
        item_name=item_name,
        seller_name=seller_name
    )
    send_email(buyer_email, subject, html)
