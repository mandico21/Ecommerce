import typing
from abc import ABC
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import find_dotenv
from pydantic import Field, PositiveInt, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class _Settings(BaseSettings, ABC):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )


class APISettings(_Settings):
    """API server settings for high-load and resilience."""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = Field(default=1, ge=1, description="Number of uvicorn workers")
    DEBUG: bool = False
    INSTANCE_APP_NAME: str = "pattern-service"

    # Timeouts
    REQUEST_TIMEOUT: int = Field(default=30, ge=1, description="Request timeout in seconds")
    GRACEFUL_SHUTDOWN_TIMEOUT: int = Field(default=30, ge=1, description="Graceful shutdown timeout")

    # Rate limiting (optional, for future use)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60


class PostgresSettings(_Settings):
    """Postgresql settings."""

    HOST: str
    PORT: int
    USER: str
    PASSWORD: SecretStr
    DATABASE_NAME: str

    MIN_CONNECTION: PositiveInt = 2
    MAX_CONNECTION: PositiveInt = 20
    MAX_IDLE: int = Field(default=300, ge=0, description="Max idle time for connections in seconds")
    TIMEOUT: int = Field(default=30, ge=1, description="Connection acquisition timeout")
    STATEMENT_TIMEOUT: int = Field(default=30000, ge=0, description="Statement timeout in milliseconds")

    DSN: typing.Optional[str] = None

    @staticmethod
    def _clean(value):
        """Trim spaces and strip surrounding quotes from env strings."""
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if (value.startswith("\"") and value.endswith("\"")) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1].strip()
        return value

    @model_validator(mode="before")
    @classmethod
    def build_dsn(cls, values: dict) -> dict:
        # normalize env values to avoid quoted DSN/credentials
        values = {k: cls._clean(v) for k, v in values.items()}
        if values.get("DSN") is not None:
            return values

        password = values.get("PASSWORD")
        password_str = (
            password.get_secret_value()
            if isinstance(password, SecretStr)
            else str(password)
        )

        values["DSN"] = str(
            PostgresDsn.build(
                scheme="postgresql",
                username=values.get("USER"),
                password=quote_plus(password_str),
                host=values.get("HOST"),
                port=int(values.get("PORT")),
                path=values.get('DATABASE_NAME'),
            )
        )
        return values


class Settings(_Settings):
    """
    Корень конфигурации. Читает .env один раз (см. lru_cache ниже).
    Вложенные секции берут переменные со своими префиксами.

    Пример: API__DEBUG, POSTGRES__DSN
    """

    API: APISettings = APISettings()
    POSTGRES: PostgresSettings


@lru_cache()
def get_settings(env_file: str | None = ".env") -> Settings:
    """
    Возвращает кэшированный инстанс Settings.
    Можно переключать файл окружения: get_settings(".env.test")
    """
    path = find_dotenv(env_file) if env_file else None
    return Settings(_env_file=path)  # type: ignore
