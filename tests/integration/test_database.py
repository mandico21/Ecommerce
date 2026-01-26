"""Интеграционные тесты для работы с БД."""

import pytest
from uuid import uuid4


@pytest.mark.integration
class TestDatabaseConnection:
    """Тесты подключения к БД."""

    async def test_connection_works(self, postgres_connector):
        """Тест: соединение с БД работает."""
        async with postgres_connector.connect() as conn:
            result = await conn.execute("SELECT 1 as value")
            row = await result.fetchone()
            assert row["value"] == 1

    async def test_healthcheck(self, postgres_connector):
        """Тест: healthcheck возвращает True."""
        result = await postgres_connector.healthcheck()
        assert result is True

    async def test_pool_stats(self, postgres_connector):
        """Тест: статистика пула доступна."""
        stats = postgres_connector.pool_stats
        assert "size" in stats
        assert "available" in stats


@pytest.mark.integration
class TestUserRepositoryIntegration:
    """Интеграционные тесты UserRepository с реальной БД."""

    async def test_create_and_get_user(
        self,
        postgres_connector,
        clean_db,
        user_factory,
    ):
        """Тест: создание и получение пользователя."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        # Create
        user = await repo.create(email="test@example.com", name="Test User")
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["id"] is not None

        # Get by ID
        from uuid import UUID
        user_id = UUID(str(user["id"]))
        found = await repo.get_by_id(user_id)
        assert found is not None
        assert found["email"] == "test@example.com"

    async def test_get_by_email(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: поиск по email."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        # Create
        await repo.create(email="findme@example.com", name="Find Me")

        # Find
        found = await repo.get_by_email("findme@example.com")
        assert found is not None
        assert found["name"] == "Find Me"

        # Not found
        not_found = await repo.get_by_email("notexists@example.com")
        assert not_found is None

    async def test_update_user(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: обновление пользователя."""
        from app.internal.repository.postgres import UserRepository
        from uuid import UUID

        repo = UserRepository(postgres_connector)

        # Create
        user = await repo.create(email="update@example.com", name="Original Name")
        user_id = UUID(str(user["id"]))

        # Update
        updated = await repo.update(user_id, name="Updated Name")
        assert updated is not None
        assert updated["name"] == "Updated Name"
        assert updated["email"] == "update@example.com"  # Не изменился

    async def test_delete_user(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: удаление пользователя."""
        from app.internal.repository.postgres import UserRepository
        from uuid import UUID

        repo = UserRepository(postgres_connector)

        # Create
        user = await repo.create(email="delete@example.com", name="To Delete")
        user_id = UUID(str(user["id"]))

        # Delete
        deleted = await repo.delete(user_id)
        assert deleted is True

        # Verify deleted
        found = await repo.get_by_id(user_id)
        assert found is None

        # Delete again (should return False)
        deleted_again = await repo.delete(user_id)
        assert deleted_again is False

    async def test_list_users(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: получение списка пользователей."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        # Create multiple users
        await repo.create(email="user1@example.com", name="User 1")
        await repo.create(email="user2@example.com", name="User 2")
        await repo.create(email="user3@example.com", name="User 3")

        # List all
        users = await repo.list_all(limit=10, offset=0)
        assert len(users) == 3

        # List with pagination
        users_page = await repo.list_all(limit=2, offset=0)
        assert len(users_page) == 2

    async def test_email_exists(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: проверка существования email."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        # Create
        await repo.create(email="exists@example.com", name="Exists")

        # Check
        assert await repo.email_exists("exists@example.com") is True
        assert await repo.email_exists("notexists@example.com") is False

    async def test_count(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: подсчёт пользователей."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        # Initially empty
        assert await repo.count() == 0

        # Create users
        await repo.create(email="count1@example.com", name="Count 1")
        await repo.create(email="count2@example.com", name="Count 2")

        # Count all
        assert await repo.count() == 2


@pytest.mark.integration
class TestTransactions:
    """Тесты транзакций."""

    async def test_transaction_commit(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: транзакция коммитится при успехе."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        async with repo.transaction() as conn:
            await conn.execute(
                "INSERT INTO users (email, name) VALUES (%s, %s)",
                ("tx@example.com", "TX User")
            )

        # Verify committed
        user = await repo.get_by_email("tx@example.com")
        assert user is not None

    async def test_transaction_rollback_on_error(
        self,
        postgres_connector,
        clean_db,
    ):
        """Тест: транзакция откатывается при ошибке."""
        from app.internal.repository.postgres import UserRepository

        repo = UserRepository(postgres_connector)

        try:
            async with repo.transaction() as conn:
                await conn.execute(
                    "INSERT INTO users (email, name) VALUES (%s, %s)",
                    ("rollback@example.com", "Rollback User")
                )
                # Вызываем ошибку
                raise Exception("Forced error")
        except Exception:
            pass

        # Verify rolled back
        user = await repo.get_by_email("rollback@example.com")
        assert user is None
