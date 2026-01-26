"""Исключения приложения."""

from app.pkg.models.exceptions.api import (
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)
from app.pkg.models.exceptions.auth import JWTError
from app.pkg.models.exceptions.payload import ErrorPayload

__all__ = [
    # Auth
    "JWTError",
    # API
    "ValidationError",
    "RateLimitError",
    "ServiceUnavailableError",
    # Payload
    "ErrorPayload",
]
