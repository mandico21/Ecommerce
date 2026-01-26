from __future__ import annotations

from typing import Any, Mapping, Self

from pydantic import BaseModel as _PydanticBaseModel, SecretBytes, SecretStr, ConfigDict


def _reveal_secrets(obj: Any) -> Any:
    """Рекурсивно разворачивает SecretStr/SecretBytes в чистые значения."""
    if isinstance(obj, SecretStr):
        return obj.get_secret_value()
    if isinstance(obj, SecretBytes):
        return obj.get_secret_value()
    if isinstance(obj, Mapping):
        return {k: _reveal_secrets(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        t = type(obj)
        return t(_reveal_secrets(x) for x in obj)
    return obj


class BaseModel(_PydanticBaseModel):
    """
    Базовая модель под Pydantic v2:
      - strict ignore лишних полей,
      - trim строк,
      - from_attributes для ORM-like объектов,
      - удобные дампы с опцией раскрытия секретов.
    """
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        # validate_assignment=True,  # включай, если хочешь валидировать при присваивании
    )

    def to_dict(self, *, show_secrets: bool = False, **dump_kwargs: Any) -> dict[str, Any]:
        """
        Дамп модели в dict. Если show_secrets=True — разворачивает SecretStr/SecretBytes.
        dump_kwargs прокинутся в model_dump (например, exclude={'password'}, exclude_none=True).
        """
        data = self.model_dump(**dump_kwargs)
        return _reveal_secrets(data) if show_secrets else data

    def to_json(self, **dump_kwargs: Any) -> str:
        """
        JSON-дамп (тонкая обёртка над model_dump_json).
        Пример: to_json(exclude_none=True)
        """
        return self.model_dump_json(**dump_kwargs)

    def without(self, *fields: str) -> Self:
        """
        Немутирующая копия без указанных полей. Если поля не заданы — глубокая копия.
        """
        if not fields:
            return self.model_copy(deep=True)
        data = self.model_dump(exclude=set(fields))
        return self.__class__.model_validate(data)
