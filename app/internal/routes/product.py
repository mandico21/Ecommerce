"""API эндпоинты для работы с продуктами."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status

from app.internal.models.product.response import ProductModelResponse
from app.internal.service.product import ProductService
from app.pkg.logger import get_logger
from app.pkg.models.base import NotFoundError

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/{product_id}",
    response_model=ProductModelResponse,
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
) -> ProductModelResponse:
    try:
        product = await product_service.get_product(product_id)

        if not product:
            raise NotFoundError(f"Продукт с ID {product_id} не найден")

        return product

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при получении продукта с ID {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
