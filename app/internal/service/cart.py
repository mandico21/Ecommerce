from uuid import UUID

from app.internal.models.cart import api, repo
from app.internal.models.cart.repo import ReadCartByIdQuery
from app.internal.repository.postgres import CartRepo
from app.pkg.logger import get_logger
from app.pkg.models.base import NotFoundError
from .product import ProductService


class CartService:
    """Сервис для работы с корзиной."""

    __logger = get_logger(__name__)

    def __init__(
        self,
        cart_repo: CartRepo,
        product_service: ProductService,
        request_id: str | None = None
    ) -> None:
        self._repo = cart_repo
        self._request_id = request_id
        self._product_service = product_service

    async def create_cart(self) -> api.CartAPIResponse:
        """Создать новую корзину."""
        self.__logger.info(
            "Создание новой корзины | request_id=%s",
            self._request_id,
        )
        cart = await self._repo.create()
        self.__logger.info(
            "Корзина успешно создана: cart_id=%s | request_id=%s",
            cart.id,
            self._request_id,
        )
        return cart.migrate(api.CartAPIResponse)

    # async def get_by_id(self, cart_id: UUID) -> api.CartByAPIResponse | None:
    #     return await self._repo.get_by_id(query=ReadCartByIdQuery(id=cart_id))

    async def get_cart(self, cart_id: UUID) -> api.CartByAPIResponse:
        cart = await self._repo.get_by_id(query=ReadCartByIdQuery(id=cart_id))

        if not cart:
            self.__logger.warning(
                "Корзина не найдена: cart_id=%s | request_id=%s",
                cart_id,
                self._request_id,
            )
            raise NotFoundError(f"Корзина с ID {cart_id} не найден")

        self.__logger.info(
            "Корзина успешно получена: cart_id=%s | request_id=%s",
            cart.id,
            self._request_id,
        )
        return cart.migrate(api.CartByAPIResponse)

    async def add_product_in_cart(
        self,
        request: api.AddProductCartAPIRequest
    ) -> api.CartByAPIResponse:
        await self._product_service.get_product(product_id=request.product_id)

        await self.get_cart(cart_id=request.cart_id)
        self.__logger.info(
            "Добавление продукта в корзину: cart_id=%s, product_id=%s, quantity=%s | request_id=%s",
            request.cart_id,
            request.product_id,
            request.quantity,
            self._request_id,
        )
        cart_items = await self._repo.add_product_in_cart(
            cmd=request.migrate(repo.AddProductCartRepoCommand),
        )

        if not cart_items:
            self.__logger.warning(
                "Не удалось добавить продукт в корзину: cart_id=%s | request_id=%s",
                request.cart_id,
                self._request_id,
            )
            raise NotFoundError(f"Не удалось добавить продукт в корзину с ID {request.cart_id}")
        self.__logger.info(
            "Продукт успешно добавлен в корзину: cart_id=%s, product_id=%s | request_id=%s",
            request.cart_id,
            request.product_id,
            self._request_id,
        )
        cart = await self.get_cart(cart_id=request.cart_id)
        return cart.migrate(api.CartByAPIResponse)
