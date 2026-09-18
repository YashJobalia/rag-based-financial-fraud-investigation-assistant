from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: SecretStr = SecretStr("")
    admin_database_url: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    auth_secret: SecretStr = SecretStr("")
    enable_public_demo: bool = False
    enable_live_generation: bool = False
    daily_generation_limit: int = 10
    input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None


@lru_cache
def settings() -> Settings:
    return Settings()
