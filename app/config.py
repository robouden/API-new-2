from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Email configuration
    # IMPORTANT: Replace these placeholder values with your actual email provider's settings.
    # For development, you can use a service like Mailtrap or Ethereal.
    # For production, use a transactional email service like SendGrid, Mailgun, or AWS SES.
    MAIL_USERNAME: str = "your-username"
    MAIL_PASSWORD: str = "your-password"
    MAIL_FROM: str = "noreply@safecast.org"
    MAIL_FROM_NAME: str = "Safecast API"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.mailtrap.io"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # If you create a .env file in the root directory, these settings will be loaded from it.
        env_file = ".env"

settings = Settings()
