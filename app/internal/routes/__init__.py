"""Регистрация маршрутов приложения."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.internal.routes.cart import router as cart_router
from app.internal.routes.product import router as product_router

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["register_routes"]


def register_routes(app: "FastAPI") -> None:
    """
    Регистрация всех маршрутов приложения.

    Централизованная точка для подключения всех API роутеров.
    При добавлении новых роутеров добавляйте их сюда.

    Аргументы:
        app: Экземпляр FastAPI приложения

    Пример:
        >>> from app.internal.routes.users import router as users_router
        >>> app.include_router(
        ...     users_router,
        ...     prefix="/api/v1/users",
        ...     tags=["users"]
        ... )

    Структура API:
        /api/v1/users      - Управление пользователями
        /api/v1/auth       - Аутентификация
        /api/v1/products   - Управление товарами
        ...
    """
    app.include_router(product_router, prefix="/api/v1/products", tags=["Product"])
    app.include_router(cart_router, prefix="/api/v1/cart", tags=["Cart"])
