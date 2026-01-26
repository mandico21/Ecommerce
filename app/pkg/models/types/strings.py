"""Кастомные строковые типы с валидацией."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, SecretStr

__all__ = ["NotEmptySecretStr", "NotEmptyStr"]


def _validate_not_empty(v: str) -> str:
    """Валидатор: строка не должна быть пустой."""
    if not v or not v.strip():
        raise ValueError("Строка не должна быть пустой")
    return v.strip()


# Pydantic v2 способ: Annotated + AfterValidator
NotEmptyStr = Annotated[str, AfterValidator(_validate_not_empty)]
"""Строка, которая не может быть пустой (с автоматическим trim)."""


class NotEmptySecretStr(SecretStr):
    """SecretStr, который не может быть пустым."""

    min_length = 1

