from __future__ import annotations

__all__ = ["collect_response"]

import dataclasses
from decimal import Decimal
from enum import Enum
from functools import wraps
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import TypeAdapter, ValidationError
from pydantic import BaseModel as PydBaseModel

from app.pkg.logger import get_logger
from app.pkg.models.base import NotFoundError

log = get_logger("app.repo.mapping")


def _postprocess_scalar(x: Any) -> Any:
    """
    Постобработка скалярных значений из БД.

    Преобразует:
    - memoryview (bytea в psycopg3) → bytes
    - Decimal → оставляем как есть (Pydantic сам решит)
    - Enum → value (строка/число)
    """
    if isinstance(x, memoryview):
        return x.tobytes()
    if isinstance(x, Decimal):
        return x
    if isinstance(x, Enum):
        return x.value
    return x


def _postprocess(obj: Any) -> Any:
    """
    Рекурсивная постобработка объектов для подготовки к валидации Pydantic.

    Преобразует:
    - Pydantic модели → dict
    - dataclass → dict
    - dict → рекурсивно обрабатывает значения
    - list/tuple/set → рекурсивно обрабатывает элементы
    - скаляры → через _postprocess_scalar
    """
    # Pydantic-модель → dict
    if isinstance(obj, PydBaseModel):
        obj = obj.model_dump()
    # dataclass → dict
    if dataclasses.is_dataclass(obj):
        obj = dataclasses.asdict(obj)
    # mapping - рекурсивная обработка значений
    if isinstance(obj, dict):
        return {k: _postprocess(v) for k, v in obj.items()}
    # последовательности - рекурсивная обработка элементов
    if isinstance(obj, (list, tuple, set)):
        t = type(obj)
        return t(_postprocess(v) for v in obj)
    # скаляры
    return _postprocess_scalar(obj)


def _is_optional(annotation: Any) -> bool:
    """
    Проверить, является ли аннотация Optional (Union с None).

    Примеры:
        Optional[User] → True
        User | None → True
        User → False
        list[User] → False
    """
    origin = get_origin(annotation)
    # Union типы (включая Optional)
    if origin is not None:
        # Для Union проверяем наличие None в args
        args = get_args(annotation)
        return type(None) in args
    return False


def _is_list_type(annotation: Any) -> bool:
    """
    Проверить, является ли аннотация списком.

    Примеры:
        list[User] → True
        List[User] → True
        User → False
        Optional[list[User]] → False (обрабатывается отдельно)
    """
    origin = get_origin(annotation)
    return origin in (list, tuple, set)


def _build_adapter(ret_annot: Any) -> TypeAdapter:
    """Создать TypeAdapter под аннотацию возврата."""
    return TypeAdapter(ret_annot)


def collect_response(fn):
    """
    Декоратор для автоматического маппинга результата репозитория в Pydantic модель.

    Функциональность:
    - Получает сырой результат (dict | list[dict] | None) из метода репозитория
    - Постобрабатывает значения (memoryview, Decimal, Enum)
    - Валидирует и преобразует в тип из аннотации возврата через Pydantic TypeAdapter
    - Обрабатывает Optional, list, Union типы
    - Кидает NotFoundError если результат пустой и тип не Optional

    Примеры аннотаций:
        async def get_user(self, id: UUID) -> User | None:
            # None разрешён, NotFoundError не будет

        async def get_user(self, id: UUID) -> User:
            # None не разрешён, будет NotFoundError если запись не найдена

        async def list_users(self) -> list[User]:
            # Пустой список [] - это норма, NotFoundError не будет

    Использование:
        @collect_response
        async def get_by_id(self, user_id: UUID) -> User | None:
            return await self.fetch_one(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
    """

    # Получаем аннотацию возврата один раз при декорировании
    hints = get_type_hints(fn, globalns=fn.__globals__, localns=None)
    ret_annot = hints.get("return", Any)

    # Анализируем тип для оптимизации логики
    is_optional = _is_optional(ret_annot)
    is_list = _is_list_type(ret_annot)

    # Создаём адаптер один раз
    adapter = _build_adapter(ret_annot)

    @wraps(fn)
    async def inner(*args, **kwargs):
        # Получаем сырой результат из репозитория
        raw = await fn(*args, **kwargs)

        # Обработка пустого результата
        if raw is None or (isinstance(raw, (list, tuple)) and len(raw) == 0):
            # Для списков пустой результат - это нормально
            if is_list:
                log.debug("Пустой список в %s", fn.__name__)
                try:
                    return adapter.validate_python([])
                except ValidationError:
                    return []

            # Для Optional типов None - это норма
            if is_optional:
                log.debug("Пустой результат (Optional) в %s", fn.__name__)
                return None

            # Для обязательных типов - это ошибка
            log.info("Запись не найдена в %s", fn.__name__)
            raise NotFoundError(
                message=f"Запись не найдена в {fn.__name__}",
                details={"method": fn.__name__, "args": str(args[1:])[:100]}
            )

        # Постобработка сырых данных
        try:
            prepared = _postprocess(raw)
        except Exception as e:
            log.error("Ошибка постобработки в %s: %r", fn.__name__, e)
            raise

        # Валидация через Pydantic
        try:
            value = adapter.validate_python(prepared)
            log.debug("Успешный маппинг в %s: %s записей", fn.__name__,
                     len(value) if isinstance(value, list) else 1)
            return value
        except ValidationError as e:
            log.error(
                "Ошибка валидации Pydantic в %s: %s | Данные: %s",
                fn.__name__,
                e.error_count(),
                str(prepared)[:200]
            )
            raise
        except Exception as e:
            log.error("Неожиданная ошибка маппинга в %s: %r", fn.__name__, e)
            raise

    return inner
