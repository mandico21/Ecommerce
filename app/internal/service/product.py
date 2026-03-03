"""Сервис для работы с продуктами."""
from app.internal.models.product.api import ProductAPIResponse, CreateProductAPIRequest
from app.internal.models.product.repository import CreateProductRepoCommand
from app.internal.repository.postgres.product import ProductRepo
from app.pkg.logger import get_logger
from app.pkg.models.base import NotFoundError


class ProductService:
    """Сервис для бизнес-логики работы с продуктами."""

    __logger = get_logger(__name__)

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
        self.__logger.info(
            "Получение продукта product_id=%s | request_id=%s",
            product_id,
            self._request_id,
        )

        product = await self._product_repository.get_product_by_id(product_id)

        if not product:
            self.__logger.warning(
                "Продукт не найден: product_id=%s | request_id=%s",
                product_id,
                self._request_id,
            )
            raise NotFoundError(f"Продукт с ID {product_id} не найден")

        self.__logger.info(
            "Продукт успешно получен: product_id=%s, name=%s | request_id=%s",
            product.id,
            product.name,
            self._request_id,
        )
        return product.migrate(ProductAPIResponse)

    async def create_product(self, request: CreateProductAPIRequest) -> ProductAPIResponse:
        """
        Создать новый продукт.

        Args:
            request: данные для создания продукта

        Returns:
            ProductAPIResponse: данные созданного продукта
        """
        self.__logger.info(f"Создание продукта {request.name} | request_id={self._request_id}")

        product = await self._product_repository.create(
            cmd=request.migrate(CreateProductRepoCommand)
        )
        return product.migrate(ProductAPIResponse)
