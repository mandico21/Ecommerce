"""Сервисный слой приложения.

Сервисы содержат бизнес-логику и оркестрируют работу репозиториев.

Пример структуры:
    app/internal/service/
    ├── __init__.py
    ├── user.py           # UserService
    ├── auth.py           # AuthService
    ├── product.py        # ProductService
    └── notification.py   # NotificationService

Пример сервиса:
    from app.internal.repository.postgres import UserRepository

    class UserService:
        def __init__(self, user_repo: UserRepository):
            self._user_repo = user_repo

        async def create_user(self, email: str, name: str) -> UserModel:
            # Бизнес-логика: валидация, проверки, создание
            if await self._user_repo.email_exists(email):
                raise ValueError("Email уже существует")
            return await self._user_repo.create(email=email, name=name)
"""

# Экспортируйте ваши сервисы здесь:
from app.internal.service.product import ProductService

__all__ = ["ProductService"]
