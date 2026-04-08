"""
Application configuration loaded from environment variables via Pydantic BaseSettings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from .env file or environment variables."""

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "help2mail"
    RATE_LIMIT_DELAY_SECONDS: int = 3
    MAX_RESUME_SIZE_MB: int = 5
    SECRET_KEY: str = "change_this_to_a_random_secret"
    ENV: str = "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def max_resume_bytes(self) -> int:
        """Return max resume size in bytes."""
        return self.MAX_RESUME_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
