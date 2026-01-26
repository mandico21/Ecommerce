"""Unit тесты для базовых моделей и исключений."""

import pytest
from http import HTTPStatus

from app.pkg.models.base import (
    BaseModel,
    BaseEnum,
    AppError,
    NotFoundError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    DependencyError,
)


@pytest.mark.unit
class TestBaseModel:
    """Тесты BaseModel."""

    def test_to_dict(self):
        """Тест: преобразование в dict."""
        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        result = model.to_dict()

        assert result == {"name": "test", "value": 42}

    def test_to_json(self):
        """Тест: преобразование в JSON строку."""
        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        result = model.to_json()

        assert '"name":"test"' in result or '"name": "test"' in result
        assert "42" in result

    def test_model_config_from_attributes(self):
        """Тест: модель создаётся из атрибутов (ORM mode)."""
        class TestModel(BaseModel):
            name: str

        # Симулируем ORM объект
        class FakeORM:
            name = "from_orm"

        model = TestModel.model_validate(FakeORM())
        assert model.name == "from_orm"


@pytest.mark.unit
class TestBaseEnum:
    """Тесты BaseEnum."""

    def test_enum_value(self):
        """Тест: получение value."""
        class Status(BaseEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        assert Status.ACTIVE.value == "active"
        assert str(Status.ACTIVE) == "active"

    def test_enum_with_label(self):
        """Тест: enum с label."""
        class Status(BaseEnum):
            ACTIVE = ("active", "Активен")
            INACTIVE = ("inactive", "Неактивен")

        assert Status.ACTIVE.value == "active"
        assert Status.ACTIVE.label == "Активен"

    def test_enum_choices(self):
        """Тест: получение choices для форм."""
        class Status(BaseEnum):
            ACTIVE = ("active", "Активен")
            INACTIVE = ("inactive", "Неактивен")

        choices = Status.choices()
        assert ("active", "Активен") in choices
        assert ("inactive", "Неактивен") in choices

    def test_enum_codes(self):
        """Тест: получение всех кодов."""
        class Status(BaseEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        codes = Status.codes()
        assert codes == {"active", "inactive"}

    def test_enum_from_code(self):
        """Тест: создание из кода."""
        class Status(BaseEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        status = Status.from_code("active")
        assert status == Status.ACTIVE


@pytest.mark.unit
class TestAppError:
    """Тесты иерархии исключений."""

    def test_app_error_defaults(self):
        """Тест: AppError с дефолтными значениями."""
        error = AppError()

        assert error.http_status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert error.message == "Internal server error"
        assert error.details == {}  # Пустой dict по умолчанию
        assert error.expose is True

    def test_app_error_custom_message(self):
        """Тест: AppError с кастомным сообщением."""
        error = AppError(message="Custom error", details={"key": "value"})

        assert error.message == "Custom error"
        assert error.details == {"key": "value"}

    def test_not_found_error(self):
        """Тест: NotFoundError."""
        error = NotFoundError(message="User not found")

        assert error.http_status == HTTPStatus.NOT_FOUND
        assert error.message == "User not found"

    def test_bad_request_error(self):
        """Тест: BadRequestError."""
        error = BadRequestError()

        assert error.http_status == HTTPStatus.BAD_REQUEST

    def test_unauthorized_error(self):
        """Тест: UnauthorizedError."""
        error = UnauthorizedError()

        assert error.http_status == HTTPStatus.UNAUTHORIZED

    def test_forbidden_error(self):
        """Тест: ForbiddenError."""
        error = ForbiddenError()

        assert error.http_status == HTTPStatus.FORBIDDEN

    def test_conflict_error(self):
        """Тест: ConflictError."""
        error = ConflictError()

        assert error.http_status == HTTPStatus.CONFLICT

    def test_dependency_error(self):
        """Тест: DependencyError с cause."""
        cause = Exception("Database connection failed")
        error = DependencyError(message="DB error", cause=cause)

        assert error.http_status == HTTPStatus.SERVICE_UNAVAILABLE
        assert error.cause is cause
        # expose зависит от реализации, проверяем только наличие атрибута
        assert hasattr(error, "expose")


@pytest.mark.unit
class TestNotEmptyStr:
    """Тесты NotEmptyStr типа."""

    def test_valid_string(self):
        """Тест: валидная строка."""
        from app.pkg.models.types import NotEmptyStr
        from pydantic import BaseModel as PydanticModel

        class TestModel(PydanticModel):
            name: NotEmptyStr

        model = TestModel(name="valid")
        assert model.name == "valid"

    def test_string_with_spaces_trimmed(self):
        """Тест: строка с пробелами обрезается."""
        from app.pkg.models.types import NotEmptyStr
        from pydantic import BaseModel as PydanticModel

        class TestModel(PydanticModel):
            name: NotEmptyStr

        model = TestModel(name="  valid  ")
        assert model.name == "valid"

    def test_empty_string_fails(self):
        """Тест: пустая строка вызывает ошибку."""
        from app.pkg.models.types import NotEmptyStr
        from pydantic import BaseModel as PydanticModel, ValidationError

        class TestModel(PydanticModel):
            name: NotEmptyStr

        with pytest.raises(ValidationError):
            TestModel(name="")

    def test_whitespace_only_fails(self):
        """Тест: строка только из пробелов вызывает ошибку."""
        from app.pkg.models.types import NotEmptyStr
        from pydantic import BaseModel as PydanticModel, ValidationError

        class TestModel(PydanticModel):
            name: NotEmptyStr

        with pytest.raises(ValidationError):
            TestModel(name="   ")
