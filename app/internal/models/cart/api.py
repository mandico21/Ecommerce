from app.internal.models.cart import BaseCart, CartFields, CartItemsFields


class CartAPIResponse(BaseCart):
    """Модель для ответа с данными корзины."""

    id: CartFields.ID
    created_at: CartFields.Created_at
    updated_at: CartFields.Updated_at


class CartItemsAPIResponse(BaseCart):
    """Модель для ответа с данными элемента корзины."""

    id: CartItemsFields.ID
    product_id: CartItemsFields.Product_id
    quantity: CartItemsFields.Quantity


class CartByAPIResponse(CartAPIResponse):
    """Модель для ответа с данными корзины и её элементов."""

    items: list[CartItemsAPIResponse]
