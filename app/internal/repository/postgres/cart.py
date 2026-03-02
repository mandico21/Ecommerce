from app.internal.models.cart.repository import (
    CartRepositoryResponse, ReadCartByIdQuery,
    CartByIdRepositoryResponse,
)
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
    async def create(self) -> CartRepositoryResponse | None:
        """Создать новую корзину и вернуть её данные."""
        sql = """
              INSERT INTO carts (created_at, updated_at)
              VALUES (NOW(), NOW())
              RETURNING id, created_at, updated_at \
              """
        res = await self.fetch_one(sql)
        logger.info(f"Новая корзина создана: {res}")
        return res

    @collect_response
    async def get_by_id(self, query: ReadCartByIdQuery) -> CartByIdRepositoryResponse | None:
        sql = """
              select c.id,
                     c.created_at,
                     c.updated_at,
                     coalesce(
                                     json_agg(
                                     json_build_object(
                                             'id', ci.id,
                                             'product_id', ci.product_id,
                                             'quantity', ci.quantity
                                     )
                                             ) filter (where ci.id is not null),
                                     '[]'
                     ) as items
              from carts c
                       left join cart_items ci on ci.cart_id = c.id
              where c.id = %s
              group by c.id; \
              """
        res = await self.fetch_all(sql, (query.id,))
        logger.info(f"Получена корзина по ID {query.id}: {res}")
        return res[0] if res else None
