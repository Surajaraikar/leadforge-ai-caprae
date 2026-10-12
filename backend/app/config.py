from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LeadForge AI API"
    database_path: Path = Path("data/leadforge.db")
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    osm_user_agent: str = "LeadForge-AI-Caprae-Assignment/1.0"
    request_timeout_seconds: float = Field(default=25.0, ge=5, le=60)
    discovery_cache_seconds: int = Field(default=900, ge=0, le=86400)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
