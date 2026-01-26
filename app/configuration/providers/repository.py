"""Провайдер репозиториев для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepository
from app.pkg.connectors.postgres import PostgresConnector


class RepositoryProvider(Provider):
    """Предоставляет экземпляры репозиториев."""

    @provide(scope=Scope.REQUEST)
    def user_repository(self, connector: PostgresConnector) -> UserRepository:
        """Предоставляет UserRepository для скоупа запроса."""
        return UserRepository(connector)
