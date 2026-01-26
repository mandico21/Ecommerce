"""Типы для работы с FastAPI."""

from typing import TypeAlias

from fastapi import FastAPI

__all__ = ["FastAPIInstance"]

# Type alias для FastAPI приложения
FastAPIInstance: TypeAlias = FastAPI
"""Алиас типа для FastAPI приложения."""
