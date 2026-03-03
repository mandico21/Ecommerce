from app.internal.models.cart import repo
from app.internal.models.cart.repo import (
    CartByIdRepositoryResponse,
    CartRepositoryResponse,
    ReadCartByIdQuery,
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
        res = await self.fetch_one(sql, (query.id,))
        logger.debug("Запрошена корзина по ID=%s | found=%s", query.id, bool(res))
        return res

    async def add_product_in_cart(
        self,
        cmd: repo.AddProductCartRepoCommand
    ) -> int | None:
        sql = """
              insert into cart_items (cart_id, product_id, quantity)
              values (%s, %s, %s)
              on conflict (cart_id, product_id) do update
                  set quantity   = cart_items.quantity + EXCLUDED.quantity,
                      updated_at = NOW()
              returning id; \
              """
        res = await self.fetch_val(sql, (cmd.cart_id, cmd.product_id, cmd.quantity))
        return int(res) if res is not None else None
