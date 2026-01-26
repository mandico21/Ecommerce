"""
Конфигурация pytest для проекта.

Содержит:
- Фикстуры для работы с БД (реальной и мок)
- Фикстуры для FastAPI TestClient
- Фикстуры для Dishka контейнера
- Утилиты для тестирования
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from dishka import AsyncContainer, make_async_container
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.configuration.providers import (
    ClientProvider,
    ConnectorsProvider,
    RepositoryProvider,
    ServiceProvider,
    SettingsProvider,
)
from app.main import create_app
from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.settings import Settings, get_settings


# ═══════════════════════════════════════════════════════════════════════════════
# Конфигурация pytest
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Регистрация кастомных маркеров."""
    config.addinivalue_line("markers", "unit: Unit тесты (без внешних зависимостей)")
    config.addinivalue_line("markers", "integration: Интеграционные тесты (с БД)")
    config.addinivalue_line("markers", "slow: Медленные тесты")


# ═══════════════════════════════════════════════════════════════════════════════
# Event Loop
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаём event loop для всей сессии тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Settings
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def settings() -> Settings:
    """Настройки приложения для тестов."""
    return get_settings()


@pytest.fixture
def test_settings(settings: Settings) -> Settings:
    """Настройки с переопределёнными значениями для тестов."""
    # Можно переопределить настройки для тестов
    return settings


# ═══════════════════════════════════════════════════════════════════════════════
# Mocks - PostgreSQL
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_postgres_connector() -> AsyncMock:
    """Мок PostgresConnector для unit тестов."""
    connector = AsyncMock(spec=PostgresConnector)
    connector.healthcheck.return_value = True
    connector.pool_stats = {"size": 5, "available": 3, "waiting": 0}

    # Мок для connect() context manager
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = AsyncMock()

    connector.connect.return_value.__aenter__.return_value = mock_connection
    connector.connect.return_value.__aexit__.return_value = None

    return connector


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Мок для AsyncConnection."""
    conn = AsyncMock()

    # Мок для execute
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.rowcount = 0
    conn.execute.return_value = mock_cursor

    # Мок для transaction
    conn.transaction.return_value.__aenter__.return_value = None
    conn.transaction.return_value.__aexit__.return_value = None

    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# Real PostgreSQL (для интеграционных тестов)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="session")
async def postgres_connector(settings: Settings) -> AsyncGenerator[PostgresConnector, None]:
    """
    Реальный PostgresConnector для интеграционных тестов.

    Использует настройки из .env или переменных окружения.
    """
    connector = PostgresConnector(
        settings=settings.POSTGRES,
        min_size=1,
        max_size=5,
    )
    await connector.startup()

    yield connector

    await connector.shutdown()


@pytest_asyncio.fixture
async def db_connection(postgres_connector: PostgresConnector):
    """Соединение с БД для интеграционных тестов."""
    async with postgres_connector.connect() as conn:
        yield conn


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI App & Client
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def app() -> FastAPI:
    """FastAPI приложение для тестов."""
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP клиент для тестирования API.

    Использует httpx.AsyncClient с ASGITransport.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(
    app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticated HTTP клиент с токеном авторизации.

    Добавьте свою логику получения токена.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        yield ac


# ═══════════════════════════════════════════════════════════════════════════════
# Dishka Container
# ═══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def container() -> AsyncGenerator[AsyncContainer, None]:
    """Dishka контейнер для тестов."""
    container = make_async_container(
        SettingsProvider(),
        ConnectorsProvider(),
        RepositoryProvider(),
        ServiceProvider(),
        ClientProvider(),
    )

    yield container

    await container.close()


@pytest_asyncio.fixture
async def mock_container(
    mock_postgres_connector: AsyncMock,
) -> AsyncGenerator[AsyncContainer, None]:
    """
    Dishka контейнер с моками для unit тестов.

    Переопределяет реальные зависимости на моки.
    """
    from dishka import Provider, Scope, provide

    class MockConnectorsProvider(Provider):
        @provide(scope=Scope.APP)
        def postgres_connector(self) -> PostgresConnector:
            return mock_postgres_connector

    container = make_async_container(
        SettingsProvider(),
        MockConnectorsProvider(),
        RepositoryProvider(),
        ServiceProvider(),
    )

    yield container

    await container.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Factories
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def user_data() -> dict:
    """Тестовые данные пользователя."""
    return {
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def user_factory():
    """
    Фабрика для создания тестовых пользователей.

    Использование:
        user = user_factory(email="custom@example.com")
    """
    from uuid import uuid4
    from datetime import datetime, timezone

    def _create_user(
        id: str | None = None,
        email: str = "test@example.com",
        name: str = "Test User",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "id": id or str(uuid4()),
            "email": email,
            "name": name,
            "created_at": created_at or now,
            "updated_at": updated_at or now,
        }

    return _create_user


# ═══════════════════════════════════════════════════════════════════════════════
# Database Cleanup (для интеграционных тестов)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def clean_db(postgres_connector: PostgresConnector):
    """
    Очистка БД перед и после теста.

    Использование:
        @pytest.mark.integration
        async def test_something(clean_db, postgres_connector):
            # БД чистая
            ...
    """
    # Перед тестом
    async with postgres_connector.connect() as conn:
        await conn.execute("TRUNCATE users RESTART IDENTITY CASCADE")

    yield

    # После теста
    async with postgres_connector.connect() as conn:
        await conn.execute("TRUNCATE users RESTART IDENTITY CASCADE")


# ═══════════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def anyio_backend() -> str:
    """Backend для anyio (используется pytest-asyncio)."""
    return "asyncio"
