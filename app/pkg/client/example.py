"""Пример HTTP клиента для внешнего API."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import SecretStr

from app.pkg.client.base import BaseApiClient, HttpResult


class ExampleApiClient(BaseApiClient):
    """
    Пример клиента для работы с внешним API.

    Демонстрирует:
    - Установку client_name и base_url
    - Добавление авторизации через default_headers
    - Обёртку методов API
    - Кастомную постобработку результатов
    """

    client_name = "ExampleAPI"
    base_url = "https://api.example.com"

    def __init__(
        self,
        *,
        api_key: SecretStr,
        base_url: str | None = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ):
        """
        Инициализация клиента.

        Аргументы:
            api_key: API ключ для авторизации
            base_url: Базовый URL (переопределяет class base_url)
            timeout: Таймаут запросов в секундах
        """
        self._api_key = api_key
        super().__init__(base_url=base_url, timeout=timeout, **kwargs)

    def default_headers(self) -> Mapping[str, str]:
        """Добавляем API ключ в заголовки всех запросов."""
        return {
            "X-API-Key": self._api_key.get_secret_value(),
            "Accept": "application/json",
        }

    def postprocess(self, result: HttpResult) -> HttpResult:
        """
        Постобработка результата.
        Например, можно нормализовать специфичные коды ответа.
        """
        # Пример: трактуем 404 как валидный ответ (ресурс не найден, но не ошибка сервера)
        if result.status == 404:
            # Можно добавить кастомную логику
            pass
        return result

    # Методы API

    async def get_user(self, user_id: int) -> HttpResult:
        """Получить информацию о пользователе по ID."""
        return await self.get(f"/api/v1/users/{user_id}")

    async def create_user(self, email: str, name: str) -> HttpResult:
        """Создать нового пользователя."""
        return await self.post(
            "/api/v1/users",
            json={"email": email, "name": name},
        )

    async def update_user(self, user_id: int, **fields: Any) -> HttpResult:
        """Обновить данные пользователя."""
        return await self.patch(
            f"/api/v1/users/{user_id}",
            json=fields,
        )

    async def delete_user(self, user_id: int) -> HttpResult:
        """Удалить пользователя."""
        return await self.delete(f"/api/v1/users/{user_id}")

    async def list_users(self, page: int = 1, limit: int = 50) -> HttpResult:
        """Получить список пользователей с пагинацией."""
        return await self.get(
            "/api/v1/users",
            params={"page": page, "limit": limit},
        )


# Пример использования:
"""
from pydantic import SecretStr

async def example_usage():
    # Вариант 1: С async context manager (рекомендуется)
    async with ExampleApiClient(
        api_key=SecretStr("your-secret-key"),
        timeout=10.0,
        log_bodies=True,
    ) as client:
        # Получить пользователя
        result = await client.get_user(123)
        if result.ok():
            user_data = result.json()
            print(f"Пользователь: {user_data}")
        else:
            print(f"Ошибка: {result.status}, {result.error}")

        # Создать пользователя
        result = await client.create_user(
            email="test@example.com",
            name="Test User"
        )
        if result.ok():
            new_user = result.json()
            print(f"Создан пользователь: {new_user}")

    # Вариант 2: Ручное управление
    client = ExampleApiClient(
        api_key=SecretStr("your-secret-key")
    )
    try:
        result = await client.get_user(123)
        # обработка результата
    finally:
        await client.close()
"""
