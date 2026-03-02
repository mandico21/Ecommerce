__all__ = ["CartFields", "BaseCart", "BaseCartItem", "CartItemsFields"]

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.pkg.models.base import BaseModel


class BaseCart(BaseModel):
    pass


class BaseCartItem(BaseModel):
    pass


class CartFields:
    ID = Annotated[UUID, Field(description="ID корзины", examples=["u-u-i-d"])]
    Created_at = Annotated[datetime, Field(
        description="Дата и время создания корзины"
    )]
    Updated_at = Annotated[datetime, Field(
        description="Дата и время последнего обновления корзины"
    )]


class CartItemsFields:
    ID = Annotated[int, Field(description="ID элемента корзины", examples=[1])]
    Cart_id = Annotated[UUID, Field(description="ID корзины", examples=["u-u-i-d"])]
    Product_id = Annotated[int, Field(description="ID продукта", examples=[1])]
    Quantity = Annotated[int, Field(description="Количество продукта", examples=[1])]
    Created_at = Annotated[datetime, Field(
        description="Дата и время создания корзины"
    )]
    Updated_at = Annotated[datetime, Field(
        description="Дата и время последнего обновления корзины"
    )]
