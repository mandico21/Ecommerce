"""API исключения для HTTP ответов."""

from http import HTTPStatus

from app.pkg.models.base import AppError

__all__ = [
    "ValidationError",
    "RateLimitError",
    "ServiceUnavailableError",
]


class ValidationError(AppError):
    """Ошибка валидации входных данных."""

    http_status = HTTPStatus.UNPROCESSABLE_ENTITY
    message = "Ошибка валидации"


class RateLimitError(AppError):
    """Превышен лимит запросов."""

    http_status = HTTPStatus.TOO_MANY_REQUESTS
    message = "Превышен лимит запросов"


class ServiceUnavailableError(AppError):
    """Сервис временно недоступен."""

    http_status = HTTPStatus.SERVICE_UNAVAILABLE
    message = "Сервис временно недоступен"
