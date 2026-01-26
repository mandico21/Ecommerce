__all__ = [
    "PostgresConnector",
]

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from app.pkg.connectors.base import BaseConnector
from app.pkg.settings.settings import PostgresSettings
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class PostgresConnector(BaseConnector[AsyncConnection]):
    """
    PostgreSQL connection pool manager with configurable parameters.
    Supports statement timeout for query protection.
    """

    def __init__(
        self,
        settings: PostgresSettings,
        min_size: int | None = None,
        max_size: int | None = None,
        max_idle: int | None = None,
        timeout: int | None = None,
        row_factory=dict_row,
        tx_per_connection: bool = False,
    ):
        self._settings = settings
        self._pool: Optional[AsyncConnectionPool] = None
        self._min_size = min_size or settings.MIN_CONNECTION
        self._max_size = max_size or settings.MAX_CONNECTION
        self._max_idle = max_idle or settings.MAX_IDLE
        self._timeout = timeout or settings.TIMEOUT
        self._statement_timeout = settings.STATEMENT_TIMEOUT
        self._row_factory = row_factory
        self._tx_per_connection = tx_per_connection

    @property
    def name(self) -> str:
        return "postgres"

    @property
    def dsn(self) -> str:
        return self._settings.DSN

    async def startup(self) -> None:
        """Initialize connection pool and validate connectivity."""
        # Build connection options with statement timeout
        options = f"-c statement_timeout={self._statement_timeout}" if self._statement_timeout else ""

        self._pool = AsyncConnectionPool(
            conninfo=self.dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            max_idle=self._max_idle,
            timeout=self._timeout,
            open=False,
            kwargs={"options": options} if options else None,
        )
        await self._pool.open()
        # Warm up: verify at least one connection works
        await self._pool.check()

    async def shutdown(self) -> None:
        """Gracefully close all pool connections."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Acquire a connection from the pool.
        Optionally wraps in transaction if tx_per_connection is True.
        """
        if self._pool is None:
            raise RuntimeError("PostgresConnector is not started")
        async with self._pool.connection() as conn:
            if self._row_factory:
                conn.row_factory = self._row_factory
            if self._tx_per_connection:
                async with conn.transaction():
                    yield conn
            else:
                yield conn

    async def healthcheck(self) -> bool:
        """
        Quick health check - executes SELECT 1.
        Returns False on any error without raising.
        """
        try:
            async with self.connect() as conn:
                await conn.execute("SELECT 1;")
            return True
        except Exception:
            return False

    @property
    def pool_stats(self) -> dict:
        """Return pool statistics for monitoring."""
        if self._pool is None:
            return {"status": "not_started"}
        return {
            "size": self._pool.get_stats().get("pool_size", 0),
            "available": self._pool.get_stats().get("pool_available", 0),
            "waiting": self._pool.get_stats().get("requests_waiting", 0),
        }
