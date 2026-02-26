from app.internal.models.cart.api import CartAPIResponse
from app.internal.repository.postgres import CartRepo
from app.pkg.logger import get_logger


class CartService:
    """Сервис для работы с корзиной."""

    __logger = get_logger(__name__)

    def __init__(self, cart_repo: CartRepo, request_id: str | None = None) -> None:
        self._cart_repo = cart_repo
        self._request_id = request_id

    async def create_cart(self) -> CartAPIResponse:
        """Создать новую корзину."""
        self.__logger.info(
            "Создание новой корзины | request_id=%s",
            self._request_id,
        )
        cart = await self._cart_repo.create()
        self.__logger.info(
            "Корзина успешно создана: cart_id=%s | request_id=%s",
            cart.id,
            self._request_id,
        )
        return cart.migrate(CartAPIResponse)
