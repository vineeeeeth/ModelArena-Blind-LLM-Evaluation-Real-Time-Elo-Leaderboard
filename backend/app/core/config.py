"""ModelArena – core configuration, loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "modelarena"
    postgres_user: str = "modelarena"
    postgres_password: str = "changeme_in_production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ──
    redis_url: str = "redis://redis:6379/0"

    # ── Auth / Security ──
    secret_key: str = "change-this-to-a-random-64-char-string"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Ollama ──
    ollama_base_url: str = "http://ollama:11434"

    # ── Optional hosted providers ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # ── Google OAuth ──
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # ── SMTP ──
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@modelarena.dev"
    smtp_tls: bool = False

    # ── Worker ──
    rating_recompute_interval_minutes: int = 5

    # ── Rate limits ──
    anon_battles_per_hour: int = 15
    user_battles_per_hour: int = 40
    ip_battles_per_hour: int = 60


@lru_cache()
def get_settings() -> Settings:
    return Settings()

