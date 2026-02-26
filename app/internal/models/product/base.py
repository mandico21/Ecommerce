__all__ = ["ProductFields"]

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field


class ProductFields:
    ID = Annotated[int, Field(description="ID продукта", examples=[1])]
    Name = Annotated[str, Field(
        description="Название продукта", max_length=150, examples=["Смартфон Apple iPhone 15"]
    )]
    Description = Annotated[str, Field(
        description="Описание продукта", max_length=1000, examples=["Новейший смартфон с передовыми технологиями"]
    )]
    Price = Annotated[Decimal, Field(
        description="Цена продукта",
        examples=[999.99],
        ge=0,  # Цена не может быть отрицательной
        decimal_places=2
    )]
    IsAvailable = Annotated[bool, Field(
        description="Доступность продукта для покупки",
        examples=[True]
    )]
    Created_at = Annotated[datetime, Field(
        description="Дата и время создания продукта"
    )]
    Updated_at = Annotated[datetime, Field(
        description="Дата и время последнего обновления продукта"
    )]
