"""Репозиторий для работы с продуктами в PostgreSQL."""

from app.internal.models.product.repository import (
    ProductRepositoryResponse,
    CreateProductRepoCommand,
)
from app.internal.repository import BaseRepository, with_retry
from app.internal.repository.postgres.handlers import collect_response
from app.pkg.connectors import PostgresConnector


class ProductRepo(BaseRepository):
    """Репозиторий для операций с продуктами в БД."""

    def __init__(self, connector: PostgresConnector) -> None:
        super().__init__(connector)

    @property
    def table_name(self) -> str:
        """Имя таблицы в БД."""
        return "products"

    @with_retry(max_attempts=3, delay=0.1)
    @collect_response
    async def get_product_by_id(
        self,
        product_id: int
    ) -> ProductRepositoryResponse | None:
        query = """
                select id, name, description, price, is_available, created_at, updated_at
                from products
                where id = %s \
                """
        res = await self.fetch_one(query, (product_id,))
        return res

    @collect_response
    async def create(self, cmd: CreateProductRepoCommand) -> ProductRepositoryResponse | None:
        query = """
                insert into products (name, description, price, is_available)
                values (%(name)s, %(description)s, %(price)s, %(is_available)s)
                returning id, name, description, price, is_available, created_at, updated_at
                """
        res = await self.fetch_one(query, cmd.to_dict())
        return res
