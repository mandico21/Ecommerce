"""Фабрика FastAPI приложения с полной production-конфигурацией."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from dishka import FromDishka, make_async_container
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.configuration.providers import (
    ClientProvider,
    ConnectorsProvider,
    RepositoryProvider,
    RequestContextProvider,
    ServiceProvider,
    SettingsProvider,
)
from app.internal.pkg.middlewares.exception_handlers import register_exception_handlers
from app.internal.pkg.middlewares.prometheus import PrometheusMiddleware, metrics_endpoint
from app.internal.pkg.middlewares.request_id import RequestIdMiddleware
from app.internal.pkg.middlewares.timeout import TimeoutMiddleware
from app.internal.routes import register_routes
from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.connectors.redis import RedisConnector
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
        RequestContextProvider(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Eager startup: создаём коннекторы до приёма трафика (пулы готовы к первому запросу)
        if hasattr(app.state, "dishka_container"):
            container = app.state.dishka_container
            async with container() as scope:
                await scope.get(PostgresConnector)
                await scope.get(RedisConnector)
            logger.info("Connectors started (Postgres, Redis)")

        yield

        # Graceful shutdown с таймаутом (избегаем зависания при «залипших» соединениях)
        if hasattr(app.state, "dishka_container"):
            container = app.state.dishka_container
            timeout = settings.API.GRACEFUL_SHUTDOWN_TIMEOUT
            try:
                await asyncio.wait_for(container.close(), timeout=timeout)
                logger.info("Dishka container closed (connectors and clients shut down)")
            except asyncio.TimeoutError:
                logger.warning(
                    "Dishka container close exceeded timeout=%ds; forcing exit",
                    timeout,
                )

    # Создаём FastAPI приложение
    application = FastAPI(
        title=settings.API.INSTANCE_APP_NAME,
        debug=settings.API.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.dishka_container = container

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
        redis: Annotated[RedisConnector, FromDishka()],
    ):
        """Readiness проба - проверяет все зависимости (Postgres, Redis при включении)."""
        checks = {
            "postgres": await postgres.healthcheck(),
            "redis": await redis.healthcheck(),
        }
        all_ok = all(checks.values())
        return {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        }

    @application.get("/health/detailed", tags=["health"])
    async def detailed_health(
        postgres: Annotated[PostgresConnector, FromDishka()],
        redis: Annotated[RedisConnector, FromDishka()],
    ):
        """Детальная проверка здоровья со статистикой пулов."""
        postgres_ok = await postgres.healthcheck()
        redis_ok = await redis.healthcheck()
        return {
            "status": "ok" if (postgres_ok and redis_ok) else "degraded",
            "postgres": {
                "healthy": postgres_ok,
                "pool": postgres.pool_stats,
            },
            "redis": {
                "healthy": redis_ok,
                "pool": redis.pool_stats,
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
