"""Middleware для таймаута запросов - защита от зависших запросов."""

from __future__ import annotations

import asyncio
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

__all__ = ["TimeoutMiddleware"]


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения времени выполнения запроса.
    Возвращает 504 Gateway Timeout если запрос превышает таймаут.
    """

    def __init__(self, app, timeout: int = 30):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={
                    "message": "Превышено время ожидания запроса",
                    "details": {"timeout_seconds": self.timeout},
                },
            )
