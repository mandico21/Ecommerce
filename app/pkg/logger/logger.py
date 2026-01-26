"""Настройка логирования для приложения."""

import logging
import sys
from enum import StrEnum
from typing import cast

__all__ = ["get_logger", "LogType", "CustomLogger"]

_LOG_FORMAT = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)

# Уровень логирования по умолчанию (можно переопределить через env)
_DEFAULT_LEVEL = "INFO"


class LogType(StrEnum):
    """Типы логов для специальной обработки."""

    BUSINESS = "BUSINESS_VALUABLE_LOG"


class CustomLogger(logging.Logger):
    """Расширенный логгер с кастомными методами."""

    def business(self, msg: str, *args, **kwargs) -> None:
        """
        Бизнес-важный лог (для алертов в Telegram и т.д.).

        Логирует с уровнем WARNING и префиксом BUSINESS_VALUABLE_LOG.
        """
        msg = f"{LogType.BUSINESS} {msg}"
        super().warning(msg, *args, **kwargs)


def _get_stream_handler() -> logging.StreamHandler:
    """Создать stream handler для вывода в консоль."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    return handler


def get_logger(name: str, level: str | None = None) -> CustomLogger:
    """
    Получить настроенный логгер.

    Аргументы:
        name: Имя логгера (обычно __name__)
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               По умолчанию берётся из переменной окружения LOG_LEVEL или INFO

    Возвращает:
        Настроенный CustomLogger

    Пример:
        >>> from app.pkg.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Сообщение")
        >>> logger.business("Важное бизнес-событие")
    """
    import os

    # Регистрируем кастомный класс логгера
    logging.setLoggerClass(CustomLogger)

    logger = cast(CustomLogger, logging.getLogger(name))

    # Добавляем handler только если его нет
    if not logger.handlers:
        logger.addHandler(_get_stream_handler())

    # Определяем уровень: аргумент > env > default
    log_level = level or os.getenv("LOG_LEVEL", _DEFAULT_LEVEL)
    logger.setLevel(log_level.upper())

    return logger
