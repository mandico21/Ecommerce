"""Провайдер для контекста запроса (request_id и другие данные)."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.pkg.middlewares.request_id import get_request_id


class RequestContextProvider(Provider):
    """Предоставляет данные из контекста запроса."""
    scope = Scope.REQUEST

    @provide
    def request_id(self) -> str | None:
        """Получить request_id из контекста текущего запроса."""
        return get_request_id()

