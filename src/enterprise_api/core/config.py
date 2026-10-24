"""Application configuration using Pydantic Settings V2.

Adheres to 12-factor application methodology, reading from environment
variables with robust fallback defaults.
"""

from typing import Literal, Union

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for TaskSphere Enterprise API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    APP_NAME: str = "TaskSphere Enterprise API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server Bind
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(
        default="enterprise-super-secret-dev-key-change-in-production-min-32-chars-long",
        description="JWT cryptographic signing secret key",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./tasksphere.db",
        description="SQLAlchemy async connection URI",
    )

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # Handled by pydantic json parsing
        raise ValueError(f"Invalid CORS format: {v}")

    # Initial Admin Seed Credentials
    FIRST_ADMIN_EMAIL: EmailStr = "admin@tasksphere.io"
    FIRST_ADMIN_PASSWORD: str = "AdminSecurePass123!"
    FIRST_ADMIN_FULL_NAME: str = "System Administrator"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


settings = Settings()
