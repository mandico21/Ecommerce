from app.internal.models.product import BaseProduct, ProductFields


class ProductAPIResponse(BaseProduct):
    """Модель для ответа с данными продукта."""

    id: ProductFields.ID
    name: ProductFields.Name
    description: ProductFields.Description | None = None
    price: ProductFields.Price
    is_available: ProductFields.IsAvailable
    created_at: ProductFields.Created_at
    updated_at: ProductFields.Updated_at


class CreateProductAPIRequest(BaseProduct):
    """Модель для запроса на создание продукта."""

    name: ProductFields.Name
    description: ProductFields.Description | None = None
    price: ProductFields.Price
    is_available: ProductFields.IsAvailable
