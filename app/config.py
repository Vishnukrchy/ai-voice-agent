"""
Centralized application configuration.

Profile selection works like Spring's `spring.profiles.active`: the
APP_ENV environment variable ("local" | "staging" | "production") decides
which .env.<profile> file gets loaded. APP_ENV itself is read from the
real process environment (never from a file) so it's always explicit at
startup — e.g. `APP_ENV=staging uvicorn app.main:app` or
`APP_ENV=staging docker compose up`.

All secrets are still loaded exclusively from environment variables / the
selected .env file — never hardcoded.
"""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_ENVIRONMENTS = {"local", "staging", "production"}

APP_ENV = os.getenv("APP_ENV", "local").strip().lower()
if APP_ENV not in VALID_ENVIRONMENTS:
    raise ValueError(
        f"Invalid APP_ENV='{APP_ENV}'. Must be one of {sorted(VALID_ENVIRONMENTS)}. "
        f"Set it via `APP_ENV=local|staging|production` before starting the app."
    )

ENV_FILE = f".env.{APP_ENV}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    environment: str = APP_ENV

    # Gemini
    gemini_api_key: str

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # ElevenLabs
    elevenlabs_api_key: str

    # Database
    database_url: str
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "voice_agent"
    mysql_user: str = "root"
    mysql_password: str = "changeme"
    mysql_root_password: str = "changeme"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # ChromaDB
    chroma_db_path: str = "./chroma_db"

    # App
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    debug: bool = False
    base_url: str = "http://localhost:8000"

    # Comma-separated list of allowed CORS origins, e.g.
    # "https://app.example.com,https://admin.example.com". "*" allows all
    # (fine for local, should be tightened for staging/production).
    cors_origins: str = "*"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing the env file on every access."""
    return Settings()


settings = get_settings()

