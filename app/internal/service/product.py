"""Сервис для работы с продуктами."""
from app.internal.models.product.api import ProductAPIResponse
from app.internal.repository.postgres.product import ProductRepo
from app.pkg.models.base import NotFoundError


class ProductService:
    """Сервис для бизнес-логики работы с продуктами."""

    def __init__(self, product_repository: ProductRepo) -> None:
        self._product_repository = product_repository

    async def get_product(self, product_id: int) -> ProductAPIResponse:
        """
        Получить продукт по ID.

        Raises:
            NotFoundError: если продукт не найден
        """
        product = await self._product_repository.get_product_by_id(product_id)

        if not product:
            raise NotFoundError(f"Продукт с ID {product_id} не найден")

        return product.migrate(ProductAPIResponse)
