from app.internal.models.product.base import ProductFields
from app.pkg.models.base import BaseModel


class ProductModelResponse(BaseModel):
    """Модель для ответа с данными продукта."""

    id: ProductFields.ID
    name: ProductFields.Name
    description: ProductFields.Description | None = None
    price: ProductFields.Price
    is_available: ProductFields.IsAvailable
    created_at: ProductFields.Created_at
    updated_at: ProductFields.Updated_at
