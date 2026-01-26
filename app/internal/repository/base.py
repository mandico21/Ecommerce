"""Базовый репозиторий с логикой повторных попыток и обработкой ошибок."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncIterator, Callable, Generic, Sequence, TypeVar

from psycopg import AsyncConnection

from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.logger import get_logger
from app.pkg.models.base import DependencyError

logger = get_logger(__name__)

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Декоратор для повторных попыток операций с БД с экспоненциальной задержкой.

    Аргументы:
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками в секундах
        backoff: Множитель задержки после каждой попытки
        exceptions: Кортеж исключений для перехвата и повтора
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Попытка %d/%d для %s: %s",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            str(e),
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "Все %d попыток исчерпаны для %s: %s",
                            max_attempts,
                            func.__name__,
                            str(e),
                        )

            raise DependencyError(
                message=f"Операция с БД не удалась после {max_attempts} попыток",
                cause=last_exception,
            )

        return wrapper

    return decorator


class BaseRepository(ABC, Generic[T]):
    """
    Базовый класс репозитория с общими операциями БД.

    Предоставляет:
    - Управление соединениями через PostgresConnector
    - Поддержка транзакций через transaction()
    - Обработка ошибок с DependencyError
    - Bulk операции (insert_many, update_many)
    - Логирование
    """

    def __init__(self, connector: PostgresConnector):
        self._connector = connector
        self._logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Возвращает имя таблицы в БД."""

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """
        Контекстный менеджер для управления транзакциями.

        Использование:
            async with repo.transaction() as conn:
                await repo.execute("INSERT ...", conn=conn)
                await repo.execute("UPDATE ...", conn=conn)
        """
        async with self._connector.connect() as conn:
            async with conn.transaction():
                yield conn

    async def execute(
        self,
        query: str,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> Any:
        """
        Выполнить запрос и вернуть результат курсора.

        Аргументы:
            query: SQL запрос
            params: Параметры запроса
            conn: Опциональное существующее соединение (для транзакций)
        """
        try:
            if conn:
                return await conn.execute(query, params)
            else:
                async with self._connector.connect() as connection:
                    return await connection.execute(query, params)
        except Exception as e:
            self._logger.error("Запрос не выполнен: %s | Ошибка: %s", query[:100], str(e))
            raise DependencyError(
                message="Ошибка выполнения запроса к БД",
                cause=e,
            ) from e

    async def fetch_one(
        self,
        query: str,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> dict | None:
        """
        Выполнить запрос и получить одну строку как dict.

        Аргументы:
            query: SQL запрос
            params: Параметры запроса
            conn: Опциональное существующее соединение (для транзакций)
        """
        try:
            if conn:
                result = await conn.execute(query, params)
                row = await result.fetchone()
            else:
                async with self._connector.connect() as connection:
                    result = await connection.execute(query, params)
                    row = await result.fetchone()
            return dict(row) if row else None
        except Exception as e:
            self._logger.error("Fetch one не выполнен: %s | Ошибка: %s", query[:100], str(e))
            raise DependencyError(
                message="Ошибка получения данных из БД",
                cause=e,
            ) from e

    async def fetch_all(
        self,
        query: str,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> list[dict]:
        """
        Выполнить запрос и получить все строки как список dict.

        Аргументы:
            query: SQL запрос
            params: Параметры запроса
            conn: Опциональное существующее соединение (для транзакций)
        """
        try:
            if conn:
                result = await conn.execute(query, params)
                rows = await result.fetchall()
            else:
                async with self._connector.connect() as connection:
                    result = await connection.execute(query, params)
                    rows = await result.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self._logger.error("Fetch all не выполнен: %s | Ошибка: %s", query[:100], str(e))
            raise DependencyError(
                message="Ошибка получения данных из БД",
                cause=e,
            ) from e

    async def fetch_val(
        self,
        query: str,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> Any:
        """
        Выполнить запрос и получить одно значение.

        Аргументы:
            query: SQL запрос
            params: Параметры запроса
            conn: Опциональное существующее соединение (для транзакций)
        """
        row = await self.fetch_one(query, params, conn)
        if row:
            return next(iter(row.values()), None)
        return None

    async def insert_many(
        self,
        records: Sequence[dict[str, Any]],
        conn: AsyncConnection | None = None,
    ) -> int:
        """
        Массовая вставка записей.

        Аргументы:
            records: Список словарей с данными для вставки
            conn: Опциональное существующее соединение (для транзакций)

        Возвращает:
            Количество вставленных записей
        """
        if not records:
            return 0

        # Получаем поля из первой записи
        fields = list(records[0].keys())
        placeholders = ", ".join([f"%({field})s" for field in fields])
        fields_str = ", ".join(fields)

        query = f"""
            INSERT INTO {self.table_name} ({fields_str})
            VALUES ({placeholders})
        """

        try:
            if conn:
                cursor = await conn.executemany(query, records)
            else:
                async with self._connector.connect() as connection:
                    cursor = await connection.executemany(query, records)
            return cursor.rowcount
        except Exception as e:
            self._logger.error("Массовая вставка не выполнена | Ошибка: %s", str(e))
            raise DependencyError(
                message="Ошибка массовой вставки в БД",
                cause=e,
            ) from e

    async def count(
        self,
        where: str | None = None,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> int:
        """
        Подсчитать количество записей.

        Аргументы:
            where: Опциональное WHERE условие (без WHERE)
            params: Параметры для WHERE
            conn: Опциональное существующее соединение

        Возвращает:
            Количество записей
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where:
            query += f" WHERE {where}"

        return await self.fetch_val(query, params, conn) or 0

    async def exists(
        self,
        where: str,
        params: tuple | dict | None = None,
        conn: AsyncConnection | None = None,
    ) -> bool:
        """
        Проверить существование записи.

        Аргументы:
            where: WHERE условие (без WHERE)
            params: Параметры для WHERE
            conn: Опциональное существующее соединение

        Возвращает:
            True если запись существует
        """
        count = await self.count(where, params, conn)
        return count > 0

