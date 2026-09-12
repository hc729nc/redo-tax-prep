import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    claude_model_id: str = "claude-sonnet-4-5"
    database_url: str = "sqlite:///./synthia.db"
    storage_root: str = "./uploads"
    tax_year: int = 2025

    # Set to true in any real (HTTPS) deployment so the session cookie is marked
    # Secure - browsers reject Secure cookies over plain http, so this must stay
    # false for local dev (http://localhost).
    cookie_secure: bool = False

    # Signs session cookies - MUST be set to a fixed value in any real deployment
    # (a fresh random default is fine for a single local dev process, but would
    # invalidate every session on every restart/redeploy in production).
    secret_key: str = secrets.token_hex(32)

    # CORS: comma-separated list of allowed frontend origins. Only matters when the
    # frontend is served from a different origin than the API - the default covers
    # local dev (Vite). Not used when the backend serves the built frontend itself.
    allowed_origins: str = "http://localhost:5173"

    # Abuse/cost protection for a publicly reachable deployment - each authenticated
    # user is capped per rolling 24h window. Generous enough for real use, low
    # enough that a single compromised/malicious account can't run up the
    # Anthropic API bill unbounded.
    max_chat_messages_per_day: int = 60
    max_uploads_per_day: int = 30

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
