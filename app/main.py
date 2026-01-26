"""Фабрика FastAPI приложения с полной production-конфигурацией."""

from __future__ import annotations

import logging
from typing import Annotated

from dishka import FromDishka, make_async_container
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.configuration.providers import (
    ClientProvider,
    ConnectorsProvider,
    RepositoryProvider,
    ServiceProvider,
    SettingsProvider,
)
from app.internal.pkg.middlewares.exception_handlers import register_exception_handlers
from app.internal.pkg.middlewares.prometheus import PrometheusMiddleware, metrics_endpoint
from app.internal.pkg.middlewares.request_id import RequestIdMiddleware
from app.internal.pkg.middlewares.timeout import TimeoutMiddleware
from app.internal.routes import register_routes
from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.logger import get_logger
from app.pkg.settings import get_settings

logger = get_logger(__name__)


def _filter_metrics_logs() -> None:
    """Фильтрация /metrics эндпоинта из логов uvicorn."""

    class EndpointFilter(logging.Filter):
        def __init__(self, excluded_paths: list[str]):
            super().__init__()
            self.excluded_paths = excluded_paths

        def filter(self, record: logging.LogRecord) -> bool:
            message = record.getMessage()
            return not any(path in message for path in self.excluded_paths)

    logging.getLogger("uvicorn.access").addFilter(
        EndpointFilter(["/metrics", "/health/liveness"])
    )


def create_app() -> FastAPI:
    """
    Фабрика FastAPI приложения:
    - Dishka DI контейнер (settings, connectors, repository, service, client)
    - Request ID middleware для трейсинга
    - Timeout middleware для защиты от зависших запросов
    - Prometheus метрики
    - Глобальные обработчики исключений
    - CORS поддержка
    - Health check эндпоинты
    """
    settings = get_settings()

    # Создаём DI контейнер со всеми провайдерами
    container = make_async_container(
        SettingsProvider(),
        ConnectorsProvider(),
        RepositoryProvider(),
        ServiceProvider(),
        ClientProvider(),
    )

    # Создаём FastAPI приложение
    application = FastAPI(
        title=settings.API.INSTANCE_APP_NAME,
        debug=settings.API.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Настраиваем Dishka DI
    setup_dishka(container, application)
    application.router.route_class = DishkaRoute

    # Регистрируем middleware (порядок важен - последний добавленный выполняется первым)
    # 1. CORS (внешний слой)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Настроить для production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request ID (для трейсинга)
    application.add_middleware(RequestIdMiddleware)

    # 3. Prometheus метрики
    application.add_middleware(
        PrometheusMiddleware,
        app_name=settings.API.INSTANCE_APP_NAME,
    )

    # 4. Timeout (внутренний слой - оборачивает обработку запроса)
    application.add_middleware(
        TimeoutMiddleware,
        timeout=settings.API.REQUEST_TIMEOUT,
    )

    # Регистрируем обработчики исключений
    register_exception_handlers(application)

    # Регистрируем маршруты
    register_routes(application)

    # Фильтруем шумные логи
    _filter_metrics_logs()

    # Health check эндпоинты
    @application.get("/health/liveness", tags=["health"])
    async def liveness():
        """Liveness проба - всегда возвращает ok если приложение запущено."""
        return {"status": "ok"}

    @application.get("/health/readiness", tags=["health"])
    async def readiness(
        postgres: Annotated[PostgresConnector, FromDishka()],
    ):
        """Readiness проба - проверяет все зависимости."""
        checks = {
            "postgres": await postgres.healthcheck(),
        }
        all_ok = all(checks.values())
        return {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        }

    @application.get("/health/detailed", tags=["health"])
    async def detailed_health(
        postgres: Annotated[PostgresConnector, FromDishka()],
    ):
        """Детальная проверка здоровья со статистикой пула."""
        return {
            "status": "ok" if await postgres.healthcheck() else "degraded",
            "postgres": {
                "healthy": await postgres.healthcheck(),
                "pool": postgres.pool_stats,
            },
        }

    # Эндпоинт метрик
    application.add_route("/metrics", metrics_endpoint, methods=["GET"])

    logger.info(
        "Приложение запущено: %s (debug=%s, timeout=%dс)",
        settings.API.INSTANCE_APP_NAME,
        settings.API.DEBUG,
        settings.API.REQUEST_TIMEOUT,
    )

    return application
