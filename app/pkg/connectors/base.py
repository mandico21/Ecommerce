# app/pkg/connectors/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator, Generic, TypeVar

T = TypeVar("T")  # тип выдаваемого ресурса (conn, channel, client, ...)


class BaseConnector(ABC, Generic[T]):
    """Единый контракт для коннекторов: управление жизненным циклом и выдача ресурса."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Человеко-читаемое имя ресурса (для логов/метрик)."""

    @property
    @abstractmethod
    def dsn(self) -> str:
        """Строка подключения (или каноническое представление параметров подключения)."""

    @abstractmethod
    async def startup(self) -> None:
        """Инициализация ресурса (создание пула/клиента). Вызывается на старте приложения."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Корректное завершение работы (закрытие пула/клиента). Вызывается при остановке приложения."""

    @abstractmethod
    @asynccontextmanager
    async def connect(self) -> AsyncIterator[T]:
        """
        Выдать «юнит работы»: соединение/канал/клиент.
        Должно гарантировать возврат ресурса/закрытие канала после использования.
        """
        yield  # pragma: no cover

    async def healthcheck(self) -> bool:
        """
        Базовый healthcheck. Конкретные коннекторы могут переопределить.
        Возвращает True/False без исключений.
        """
        return True
