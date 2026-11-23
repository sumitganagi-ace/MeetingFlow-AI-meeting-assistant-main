
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///meeting_assistant.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AI_PROVIDER = os.getenv("AI_PROVIDER", "demo").strip().lower()

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    # Allow 10 MB attachments plus multipart form overhead.
    MAX_CONTENT_LENGTH = 11 * 1024 * 1024

    # Session security settings.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
