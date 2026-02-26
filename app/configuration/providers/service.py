"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres.product import ProductRepo
from app.internal.service.product import ProductService


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""
    scope = Scope.REQUEST

    @provide
    def product_service(
        self,
        product_repo: ProductRepo,
        request_id: str | None,
    ) -> ProductService:
        return ProductService(
            product_repository=product_repo,
            request_id=request_id,
        )
