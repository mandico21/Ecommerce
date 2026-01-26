"""Типы для Pydantic моделей и FastAPI."""

from app.pkg.models.types.fastapi import FastAPIInstance
from app.pkg.models.types.schemas import (
    CreateUser,
    CreatedAt,
    IsActive,
    IsDeleted,
    UpdatedAt,
    UpdateUser,
)
from app.pkg.models.types.strings import NotEmptySecretStr, NotEmptyStr

__all__ = [
    # FastAPI
    "FastAPIInstance",
    # Аннотации полей
    "CreatedAt",
    "UpdatedAt",
    "IsDeleted",
    "CreateUser",
    "UpdateUser",
    "IsActive",
    # Строковые типы
    "NotEmptyStr",
    "NotEmptySecretStr",
]
