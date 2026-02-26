"""API эндпоинты для работы с продуктами."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from app.internal.models.product.api import ProductAPIResponse
from app.internal.service.product import ProductService
from app.pkg.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/{product_id}",
    response_model=ProductAPIResponse,
    summary="Получить продукт по ID",
    description="Возвращает детальную информацию о продукте",
    responses={
        200: {"description": "Продукт успешно найден"},
        404: {"description": "Продукт не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    }
)
@inject
async def get_product(
    product_id: int,
    product_service: Annotated[ProductService, FromDishka()],
) -> ProductAPIResponse:
    """Получить продукт по ID. NotFoundError будет обработана глобальным обработчиком."""
    return await product_service.get_product(product_id)
