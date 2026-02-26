"""Глобальные обработчики исключений для FastAPI приложения."""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from fastapi import Request
from fastapi.responses import JSONResponse

from app.internal.pkg.middlewares.request_id import get_request_id
from app.pkg.logger import get_logger
from app.pkg.models.base import AppError, DependencyError
from app.pkg.models.exceptions import ErrorPayload

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["register_exception_handlers"]

logger = get_logger(__name__)


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """Обработка ошибок уровня приложения с логированием и корректным ответом."""
    request_id = get_request_id()

    # Логируем с соответствующим уровнем
    if exc.http_status >= 500:
        logger.error(
            "AppError [%s]: %s | request_id=%s | details=%s",
            exc.__class__.__name__,
            exc.message,
            request_id,
            exc.details,
            exc_info=exc.cause,
        )
    else:
        logger.info(
            "AppError [%s]: %s | request_id=%s",
            exc.__class__.__name__,
            exc.message,
            request_id,
        )

    payload = ErrorPayload(
        message=exc.message if exc.expose else "Внутренняя ошибка сервера",
        details=exc.details if exc.expose else None,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=payload.to_dict(),
    )


async def _handle_dependency_error(request: Request, exc: DependencyError) -> JSONResponse:
    """Обработка ошибок внешних зависимостей (БД, Redis и т.д.)."""
    request_id = get_request_id()

    logger.error(
        "DependencyError: %s | request_id=%s | cause=%s",
        exc.message,
        request_id,
        exc.cause,
        exc_info=True,
    )

    payload = ErrorPayload(
        message="Сервис временно недоступен",
        details=exc.details if exc.expose else None,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=503,
        content=payload.to_dict(),
    )


async def _handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Обработка необработанных исключений - логируем полный traceback, возвращаем общую ошибку."""
    request_id = get_request_id()

    logger.critical(
        "Необработанное исключение: %s | request_id=%s\n%s",
        str(exc),
        request_id,
        traceback.format_exc(),
    )

    payload = ErrorPayload(
        message="Внутренняя ошибка сервера",
        details=None,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=500,
        content=payload.to_dict(),
    )


def register_exception_handlers(app: "FastAPI") -> None:
    """Регистрация всех обработчиков исключений в FastAPI приложении."""
    # ВАЖНО: Порядок регистрации - от более специфичных к более общим
    app.add_exception_handler(DependencyError, _handle_dependency_error)
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(Exception, _handle_unhandled_exception)
