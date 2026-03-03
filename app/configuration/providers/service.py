"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import CartRepo
from app.internal.repository.postgres.product import ProductRepo
from app.internal.service import CartService
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

    @provide
    def cart_service(
        self,
        cart_repo: CartRepo,
        product_service: ProductService,
        request_id: str | None,
    ) -> CartService:
        return CartService(
            cart_repo=cart_repo,
            product_service=product_service,
            request_id=request_id,
        )
