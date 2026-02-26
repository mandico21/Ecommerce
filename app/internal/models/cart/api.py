from app.internal.models.cart import BaseCart, CartFields


class CartAPIResponse(BaseCart):
    """Модель для ответа с данными корзины."""

    id: CartFields.ID
    created_at: CartFields.Created_at
    updated_at: CartFields.Updated_at
