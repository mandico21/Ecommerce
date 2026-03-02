from app.internal.models.cart import BaseCart, CartFields, CartItemsFields, BaseCartItem


class CartRepositoryResponse(BaseCart):
    """Модель для ответа с данными корзины."""

    id: CartFields.ID
    created_at: CartFields.Created_at
    updated_at: CartFields.Updated_at


class CartItemRepositoryResponse(BaseCartItem):
    """Модель для ответа с данными элемента корзины."""

    id: CartItemsFields.ID
    product_id: CartItemsFields.Product_id
    quantity: CartItemsFields.Quantity


class CartByIdRepositoryResponse(CartRepositoryResponse):
    """Модель для ответа с данными корзины по ID."""

    items: list[CartItemRepositoryResponse]


class ReadCartByIdQuery(BaseCart):
    """Модель для запроса на получение корзины по ID."""

    id: CartFields.ID
