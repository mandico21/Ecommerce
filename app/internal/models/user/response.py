"""Response модели для User API."""

from datetime import datetime
from uuid import UUID

from app.pkg.models.base import BaseModel


class UserResponse(BaseModel):
    """Модель ответа для пользователя."""

    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Модель ответа для списка пользователей с пагинацией."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int
