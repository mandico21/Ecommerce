"""Сервис для работы с продуктами."""

from app.internal.models.product.response import ProductModelResponse
from app.internal.repository.postgres.product import ProductRepo


class ProductService:
    """Сервис для бизнес-логики работы с продуктами."""

    def __init__(self, product_repository: ProductRepo) -> None:
        self._product_repository = product_repository

    async def get_product(self, product_id: int) -> ProductModelResponse | None:
        return await self._product_repository.get_product_by_id(product_id)
