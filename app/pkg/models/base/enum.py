from __future__ import annotations

__all__ = ["BaseEnum"]

from enum import StrEnum


class BaseEnum(StrEnum):
    """
    Строковый Enum с поддержкой label.
    - value / code: машинное значение (str)
    - label: человеко читаемая подпись (str)
    """

    def __new__(cls, value: str | tuple[str, str], label: str | None = None):
        if isinstance(value, tuple):
            code, label = value
        else:
            code = value
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.label = label or code  # динамический атрибут инстанса
        return obj

    @property
    def code(self) -> str:
        return self.value

    # Предсказуемо: str(enum) -> "value"
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{type(self).__name__}.{self.name}(value={self.value!r}, label={self.label!r})"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """[(value, label), ...] — удобно для форм / валидации / OpenAPI."""
        return [(m.value, m.label) for m in cls]

    @classmethod
    def codes(cls) -> set[str]:
        return {m.value for m in cls}

    @classmethod
    def from_code(cls, code: str) -> BaseEnum:
        """Семантичная обёртка вокруг cls(code)."""
        return cls(code)
