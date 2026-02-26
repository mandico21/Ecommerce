"""Провайдер репозиториев для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepository, CartRepo
from app.internal.repository.postgres.product import ProductRepo
from app.pkg.connectors.postgres import PostgresConnector


class RepositoryProvider(Provider):
    """Предоставляет экземпляры репозиториев."""

    scope = Scope.REQUEST

    @provide
    def user_repository(self, connector: PostgresConnector) -> UserRepository:
        """Предоставляет UserRepository для скоупа запроса."""
        return UserRepository(connector=connector)

    @provide
    def product_repository(self, connector: PostgresConnector) -> ProductRepo:
        """Предоставляет ProductRepo для скоупа запроса."""
        return ProductRepo(connector=connector)

    @provide
    def cart_repository(self, connector: PostgresConnector) -> CartRepo:
        """Предоставляет CartRepo для скоупа запроса."""
        return CartRepo(connector=connector)
