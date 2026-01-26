"""Unit тесты для UserRepository."""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.internal.repository.postgres.user import UserRepository
from app.pkg.models.base import DependencyError


@pytest.mark.unit
class TestUserRepository:
    """Тесты UserRepository с моками."""

    @pytest.fixture
    def repository(self, mock_postgres_connector: AsyncMock) -> UserRepository:
        """Создаём репозиторий с мок-коннектором."""
        return UserRepository(mock_postgres_connector)

    @pytest.fixture
    def mock_user(self, user_factory) -> dict:
        """Тестовый пользователь."""
        return user_factory()

    # ─────────────────────────────────────────────────────────────────────────
    # get_by_id
    # ─────────────────────────────────────────────────────────────────────────

    async def test_get_by_id_found(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
        mock_user: dict,
    ):
        """Тест: пользователь найден по ID."""
        # Arrange
        user_id = uuid4()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_user

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.get_by_id(user_id)

        # Assert
        assert result is not None
        assert result["email"] == mock_user["email"]
        mock_conn.execute.assert_called_once()

    async def test_get_by_id_not_found(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: пользователь не найден."""
        # Arrange
        user_id = uuid4()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.get_by_id(user_id)

        # Assert
        assert result is None

    # ─────────────────────────────────────────────────────────────────────────
    # get_by_email
    # ─────────────────────────────────────────────────────────────────────────

    async def test_get_by_email_found(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
        mock_user: dict,
    ):
        """Тест: пользователь найден по email."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_user

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.get_by_email("test@example.com")

        # Assert
        assert result is not None
        assert result["email"] == mock_user["email"]

    # ─────────────────────────────────────────────────────────────────────────
    # create
    # ─────────────────────────────────────────────────────────────────────────

    async def test_create_success(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
        mock_user: dict,
    ):
        """Тест: успешное создание пользователя."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_user

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.create(email="test@example.com", name="Test User")

        # Assert
        assert result is not None
        assert result["email"] == mock_user["email"]
        assert result["name"] == mock_user["name"]

    # ─────────────────────────────────────────────────────────────────────────
    # delete
    # ─────────────────────────────────────────────────────────────────────────

    async def test_delete_success(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: успешное удаление пользователя."""
        # Arrange
        user_id = uuid4()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": str(user_id)}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.delete(user_id)

        # Assert
        assert result is True

    async def test_delete_not_found(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: удаление несуществующего пользователя."""
        # Arrange
        user_id = uuid4()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.delete(user_id)

        # Assert
        assert result is False

    # ─────────────────────────────────────────────────────────────────────────
    # email_exists
    # ─────────────────────────────────────────────────────────────────────────

    async def test_email_exists_true(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: email существует."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 1}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.email_exists("test@example.com")

        # Assert
        assert result is True

    async def test_email_exists_false(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: email не существует."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 0}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.email_exists("test@example.com")

        # Assert
        assert result is False


@pytest.mark.unit
class TestUserRepositoryListMethods:
    """Тесты методов списков UserRepository."""

    @pytest.fixture
    def repository(self, mock_postgres_connector: AsyncMock) -> UserRepository:
        return UserRepository(mock_postgres_connector)

    async def test_list_all_empty(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
    ):
        """Тест: пустой список пользователей."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.list_all()

        # Assert
        assert result == []

    async def test_list_all_with_data(
        self,
        repository: UserRepository,
        mock_postgres_connector: AsyncMock,
        user_factory,
    ):
        """Тест: список с пользователями."""
        # Arrange
        users = [
            user_factory(email="user1@example.com"),
            user_factory(email="user2@example.com"),
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = users

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_postgres_connector.connect.return_value.__aenter__.return_value = mock_conn

        # Act
        result = await repository.list_all(limit=10, offset=0)

        # Assert
        assert len(result) == 2
        assert result[0]["email"] == "user1@example.com"
