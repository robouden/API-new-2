from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from .config import settings
from .models import User

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_signup_confirmation(email_to: str, user: User):
    template_body = f"""
    <html>
        <body>
            <h2>Welcome to Safecast!</h2>
            <p>Thank you for signing up. Your account has been created successfully.</p>
            <p>Here is your API key, keep it safe:</p>
            <p><code>{user.api_key}</code></p>
            <p>You can now log in to the dashboard and start uploading your bGeigie data.</p>
            <p>Thanks,</p>
            <p>The Safecast Team</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Welcome to Safecast - Account Confirmation",
        recipients=[email_to],
        body=template_body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
