from typing import Any, Mapping, Self, TypeVar
from urllib.parse import urlencode

from pydantic import BaseModel as _PydanticBaseModel, SecretBytes, SecretStr, ConfigDict

Model = TypeVar("Model", bound="BaseModel")


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
      - удобные дампы с опцией раскрытия секретов,
      - методы для миграции между моделями,
      - поддержка query параметров.
    """
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        # validate_assignment=True,  # включай, если хочешь валидировать при присваивании
    )

    def to_dict(
        self,
        *,
        show_secrets: bool = False,
        skip_nulls: bool = False,
        **dump_kwargs: Any
    ) -> dict[str, Any]:
        """
        Дамп модели в dict. Если show_secrets=True — разворачивает SecretStr/SecretBytes.
        skip_nulls=True — пропускает None значения.
        dump_kwargs прокинутся в model_dump (например, exclude={'password'}, exclude_none=True).
        """
        data = self.model_dump(**dump_kwargs)
        if skip_nulls:
            data = {k: v for k, v in data.items() if v is not None}
        return _reveal_secrets(data) if show_secrets else data

    def to_json(self, **dump_kwargs: Any) -> str:
        """
        JSON-дамп (тонкая обёртка над model_dump_json).
        Пример: to_json(exclude_none=True)
        """
        return self.model_dump_json(**dump_kwargs)

    def to_query_params(
        self,
        *,
        show_secrets: bool = False,
        without_none: bool = True,
        **kwargs: Any
    ) -> str:
        """
        Преобразовать модель в URL query параметры.

        Args:
            show_secrets: показывать ли значения SecretStr/SecretBytes
            without_none: исключать ли None значения
            **kwargs: дополнительные параметры для to_dict

        Examples:
            >>> model = MyModel(name="John", age=30, email=None)
            >>> model.to_query_params()
            'name=John&age=30'
        """
        data = self.to_dict(show_secrets=show_secrets, **kwargs)
        if without_none:
            data = {k: v for k, v in data.items() if v is not None}
        return urlencode(data, doseq=True)

    def without(self, *fields: str) -> Self:
        """
        Немутирующая копия без указанных полей. Если поля не заданы — глубокая копия.
        """
        if not fields:
            return self.model_copy(deep=True)
        data = self.model_dump(exclude=set(fields))
        return self.__class__.model_validate(data)

    def migrate(
        self,
        model: type[Model],
        *,
        match_keys: dict[str, str] | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> Model:
        """
        Мигрировать одну модель в другую, игнорируя несовпадения полей.

        Args:
            model: целевая модель (наследник BaseModel)
            match_keys: маппинг полей (ключ: имя в текущей модели, значение: имя в целевой)
            extra_fields: дополнительные поля для целевой модели

        Returns:
            Экземпляр целевой модели

        Examples:
            >>> class UserA(BaseModel):
            ...     id: int
            ...     name: str
            ...     email: str

            >>> class UserB(BaseModel):
            ...     user_id: int
            ...     full_name: str

            >>> user_a = UserA(id=1, name="John", email="john@example.com")
            >>> user_b = user_a.migrate(
            ...     UserB,
            ...     match_keys={"user_id": "id", "full_name": "name"}
            ... )
            >>> # user_b = UserB(user_id=1, full_name="John")
        """
        if match_keys is None:
            match_keys = {}
        if extra_fields is None:
            extra_fields = {}

        # Получаем dict текущей модели
        self_dict = self.to_dict(show_secrets=True)

        # Применяем маппинг полей
        for target_field, source_field in match_keys.items():
            if source_field in self_dict:
                self_dict[target_field] = self_dict.pop(source_field)

        # Добавляем дополнительные поля
        self_dict.update(extra_fields)

        # Валидируем и возвращаем экземпляр целевой модели
        return model.model_validate(self_dict)

    @classmethod
    def field_getter(cls, field_name: str) -> Any:
        """
        Получить тип поля из аннотаций класса.

        Args:
            field_name: имя поля (атрибута)

        Returns:
            Тип поля из аннотаций

        Raises:
            AttributeError: если поле не найдено

        Examples:
            >>> class User(BaseModel):
            ...     id: int
            ...     name: str

            >>> User.field_getter("id")
            <class 'int'>
        """
        if not hasattr(cls, "__annotations__"):
            raise AttributeError(f"{cls.__name__} не имеет аннотаций")

        field = cls.__annotations__.get(field_name)
        if field is None:
            raise AttributeError(
                f"Поле '{field_name}' не найдено в {cls.__name__}. "
                f"Доступные поля: {list(cls.__annotations__.keys())}"
            )
        return field


