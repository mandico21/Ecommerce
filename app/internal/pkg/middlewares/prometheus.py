"""Prometheus метрики middleware и эндпоинт."""

from __future__ import annotations

import time
from typing import Callable

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["PrometheusMiddleware", "metrics_endpoint", "REGISTRY"]

# Метрики
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Общее количество HTTP запросов",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Латентность HTTP запросов в секундах",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Количество HTTP запросов в обработке",
    ["method", "endpoint"],
)


def _get_path_template(request: Request) -> str:
    """Получить шаблон пути для метрик (избегаем взрыва кардинальности)."""
    # Используем путь роута если доступен (например, /users/{user_id})
    if hasattr(request, "scope") and "route" in request.scope:
        route = request.scope["route"]
        if hasattr(route, "path"):
            return route.path
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора Prometheus метрик HTTP запросов."""

    def __init__(self, app, app_name: str = "fastapi"):
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        path = _get_path_template(request)

        # Пропускаем сам эндпоинт метрик
        if path == "/metrics":
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            duration = time.perf_counter() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()

        return response


async def metrics_endpoint(request: Request) -> Response:
    """Эндпоинт Prometheus метрик."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
