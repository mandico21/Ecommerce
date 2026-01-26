"""Провайдер коннекторов для DI контейнера."""

from __future__ import annotations

from typing import AsyncIterator

from dishka import Provider, Scope, provide

from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.settings import Settings


class ConnectorsProvider(Provider):
    """Предоставляет коннекторы к БД и внешним сервисам с управлением жизненным циклом."""

    @provide(scope=Scope.APP)
    async def postgres_connector(self, settings: Settings) -> AsyncIterator[PostgresConnector]:
        """
        Предоставляет пул соединений PostgreSQL.
        Пул запускается при первом запросе и закрывается при остановке приложения.
        """
        connector = PostgresConnector(
            settings=settings.POSTGRES,
            min_size=settings.POSTGRES.MIN_CONNECTION,
            max_size=settings.POSTGRES.MAX_CONNECTION,
        )
        await connector.startup()
        try:
            yield connector
        finally:
            await connector.shutdown()
