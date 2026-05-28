"""app/core/config.py — All settings, validated at startup."""

import json
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Google AI
    google_api_key: str = Field(...)
    llm_model: str = Field(default="gemini-2.5-flash")
    embedding_model: str = Field(default="gemini-embedding-001")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"
    )

    # Auth
    secret_key: str = Field(default="change-me")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)

    # Retrieval
    retrieval_top_k: int = Field(default=5, ge=1)
    retrieval_candidate_k: int = Field(default=12, ge=1)
    retrieval_score_threshold: float = Field(default=0.35, ge=0, le=1)
    retrieval_diversity_threshold: float = Field(default=0.85, ge=0, le=1)
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=200, ge=0)
    max_retries: int = Field(default=3, ge=0)

    # App
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Accept either a JSON string '["url"]' or a plain comma-separated string or a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_settings(self):
        if self.is_production and self.secret_key in {
            "change-me",
            "change-me-to-a-long-random-string-in-production",
        }:
            raise ValueError("SECRET_KEY must be replaced when APP_ENV=production")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.retrieval_candidate_k < self.retrieval_top_k:
            raise ValueError("RETRIEVAL_CANDIDATE_K must be at least RETRIEVAL_TOP_K")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
