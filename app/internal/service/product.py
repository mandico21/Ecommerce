"""Сервис для работы с продуктами."""
from app.internal.models.product.api import ProductAPIResponse
from app.internal.repository.postgres.product import ProductRepo
from app.pkg.logger import get_logger
from app.pkg.models.base import NotFoundError

logger = get_logger(__name__)


class ProductService:
    """Сервис для бизнес-логики работы с продуктами."""

    def __init__(
        self,
        product_repository: ProductRepo,
        request_id: str | None = None,
    ) -> None:
        self._product_repository = product_repository
        self._request_id = request_id

    async def get_product(self, product_id: int) -> ProductAPIResponse:
        """
        Получить продукт по ID.

        Raises:
            NotFoundError: если продукт не найден
        """
        logger.info(
            "Получение продукта product_id=%s | request_id=%s",
            product_id,
            self._request_id,
        )

        product = await self._product_repository.get_product_by_id(product_id)

        if not product:
            logger.warning(
                "Продукт не найден: product_id=%s | request_id=%s",
                product_id,
                self._request_id,
            )
            raise NotFoundError(f"Продукт с ID {product_id} не найден")

        logger.info(
            "Продукт успешно получен: product_id=%s, name=%s | request_id=%s",
            product.id,
            product.name,
            self._request_id,
        )
        return product.migrate(ProductAPIResponse)
