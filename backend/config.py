from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./skillmatch.db"

    # Auth
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@skillmatch.ai"
    MAIL_FROM_NAME: str = "SkillMatch AI"
    MAIL_SERVER: str = "smtp.sendgrid.net"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # App
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8000"

    # Feature Flags
    # When the real query comes back empty, the dashboard and the headcount table
    # used to substitute hard-coded sample rows - candidate names, interview times,
    # activity log entries and FTE figures - which read as real data. Off by
    # default; set DEMO_DATA=true to get the showcase numbers back.
    DEMO_DATA: bool = False
    ENABLE_CAMPAIGN_QR: bool = True
    ENABLE_OCR_ONBOARDING: bool = True
    ENABLE_SALARY_APPROVAL: bool = True
    ENABLE_AUDIT_LOGGING: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
