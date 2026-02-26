from app.internal.models.cart.repository import CartRepositoryResponse
from app.internal.repository import BaseRepository
from app.internal.repository.postgres.handlers import collect_response
from app.pkg.logger import get_logger

logger = get_logger(__name__)


class CartRepo(BaseRepository):
    """Репозиторий для операций с корзиной в БД."""

    @property
    def table_name(self) -> str:
        """Имя таблицы в БД."""
        return "carts"

    @collect_response
    async def create(self) -> CartRepositoryResponse:
        """Создать новую корзину и вернуть её данные."""
        query = """
                INSERT INTO carts (created_at, updated_at)
                VALUES (NOW(), NOW())
                RETURNING id, created_at, updated_at \
                """
        res = await self.fetch_one(query)
        logger.info(f"Новая корзина создана: {res}")
        return res
