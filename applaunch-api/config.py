# applaunch-api/config.py
"""Application settings loaded from environment variables via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_key: str                    # service role key (server-side only)
    supabase_jwt_secret: str             # used to verify Supabase JWTs

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # AWS
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    s3_bucket_sources: str = "applaunch-sources"
    s3_bucket_artifacts: str = "applaunch-artifacts"
    kms_key_arn: str

    # App
    environment: str = "development"
    api_secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once at startup)."""
    return Settings()
