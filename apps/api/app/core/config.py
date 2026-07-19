from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or root .env."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Quant Web3 Research API"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = "mysql+pymysql://quant:quant@127.0.0.1:3306/quant_web3"
    redis_url: str = "redis://127.0.0.1:6379/0"
    job_mode: str = "inline"
    artifact_dir: Path = REPOSITORY_ROOT / "data" / "reports"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_chain_ids: str = "56,97"
    siwe_domain: str = "localhost:5173"
    siwe_uri: str = "http://localhost:5173"
    siwe_statement: str = "Sign in to save and reproduce quantitative research experiments."
    challenge_ttl_seconds: int = 300

    session_cookie_name: str = "qwr_session"
    session_ttl_hours: int = 168
    session_cookie_secure: bool = False
    admin_api_key: str = "change-me-in-production"
    create_tables_on_startup: bool = True

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @computed_field
    @property
    def allowed_chain_id_set(self) -> set[int]:
        return {int(item.strip()) for item in self.allowed_chain_ids.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
