from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    claude_model_id: str = "claude-sonnet-4-5"
    database_url: str = "sqlite:///./synthia.db"
    storage_root: str = "./uploads"
    tax_year: int = 2025


@lru_cache
def get_settings() -> Settings:
    return Settings()
