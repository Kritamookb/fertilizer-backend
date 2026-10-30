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
    # Required: no fallback, so a deployment can never run with a publicly known signing key
    jwt_secret: str = Field(..., min_length=32, description="Random secret for signing admin JWTs")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    commission_rate_per_unit: int = 25
    max_agents: int = 50

    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    # Only needed to create the first admin on an empty database (see app/seed.py)
    admin_password: str | None = None

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

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if "change-me" in value.lower():
            raise ValueError("JWT_SECRET is still the example value; generate a random secret")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
