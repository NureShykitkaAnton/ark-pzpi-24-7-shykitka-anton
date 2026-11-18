"""Конфігурація серверної частини програмної системи EnergyMonitor."""

import json
from pathlib import Path
from typing import Annotated, Any

from pydantic import BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str]:
    """Перетворює рядок або JSON-список дозволених джерел CORS у список рядків."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list):
        return v
    return json.loads(v) if isinstance(v, str) else []


ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Налаштування середовища виконання та підключення до СУБД PostgreSQL 18."""

    model_config = SettingsConfigDict(
        env_file=ENV_PATH if ENV_PATH.exists() else ".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "EnergyMonitor"
    ENVIRONMENT: str = "development"

    # Налаштування реляційної СУБД PostgreSQL 18
    POSTGRES_USER: str = "pguser"
    POSTGRES_PASSWORD: str = "changeme123!0"
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "energymon"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """Формує рядок асинхронного підключення SQLAlchemy через драйвер asyncpg."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Параметри безпеки, хешування та JWT-токенів
    SECRET_KEY: str = "super-secret-dev-jwt-key-replace-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # Налаштування CORS
    CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = [
        "https://energymon.localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    FRONTEND_URL: str = "https://energymon.localhost"

    # Налаштування електронної пошти
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@energymon.com"
    MAIL_PORT: int = 1026
    MAIL_SERVER: str = "localhost"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = False
    MAIL_FROM_NAME: str = "EnergyMonitor Support"

    # Налаштування LLM-аналітики та директорії резервних копій
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    BACKUP_DIR: str = "backups"

    @property
    def is_production(self) -> bool:
        """Перевіряє, чи працює сервер у продуктивному контурі."""
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
