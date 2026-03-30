from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Fertilizer Backend"
    api_prefix: str = ""
    debug: bool = False

    database_url: str = Field(..., description="PostgreSQL connection URL")
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    commission_rate_per_unit: int = 25
    max_agents: int = 50

    admin_username: str = "admin"
    admin_email: str = "admin@gmail.com"
    admin_password: str = "change-me"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "https://fertilizer.connect2play.site",
            "http://fertilizer.connect2play.site",
        ]
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
