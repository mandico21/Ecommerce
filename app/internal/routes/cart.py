"""API эндпоинты для работы с продуктами."""
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from app.internal.models.cart.api import CartAPIResponse
from app.internal.service import CartService
from app.pkg.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/create", summary="Создать корзину", description="Создает новую корзину и возвращает ее ID",
    response_model=CartAPIResponse
)
@inject
async def create_cart(
    cart_service: Annotated[CartService, FromDishka()]
) -> CartAPIResponse:
    """Создать новую корзину."""
    return await cart_service.create_cart()
