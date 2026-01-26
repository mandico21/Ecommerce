"""Базовые модели и исключения."""

from app.pkg.models.base.enum import BaseEnum
from app.pkg.models.base.exception import (
    AppError,
    BadRequestError,
    ConflictError,
    DependencyError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from app.pkg.models.base.model import BaseModel

__all__ = [
    # Enum
    "BaseEnum",
    # Модель
    "BaseModel",
    # Исключения
    "AppError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "DependencyError",
]
