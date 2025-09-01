from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Email configuration
    # SendGrid SMTP settings
    MAIL_USERNAME: str = "apikey"
    MAIL_PASSWORD: str = "your-sendgrid-api-key"
    MAIL_FROM: str = "rob@yr-design.biz"
    MAIL_FROM_NAME: str = "Safecast API"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.sendgrid.net"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # If you create a .env file in the root directory, these settings will be loaded from it.
        env_file = ".env"

settings = Settings()
