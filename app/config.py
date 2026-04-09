from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Cripto Brasil Intel'
    app_version: str = 'v10'
    environment: str = 'development'
    port: int = 8000
    cache_ttl_seconds: int = 900
    market_cache_ttl_seconds: int = 300
    request_timeout_seconds: float = 12.0
    max_articles: int = 36
    refresh_on_startup: bool = True
    backend_url: str = 'http://localhost:8000'
    auto_approve: bool = False
    anthropic_api_key: str = ''
    openai_api_key: str = ''
    data_dir: Path = Field(default=Path('data'))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
