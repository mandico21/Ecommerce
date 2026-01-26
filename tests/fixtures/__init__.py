"""Фикстуры для тестов."""

from tests.fixtures.data import (
    SAMPLE_USERS,
    HEALTH_RESPONSE_OK,
    HEALTH_RESPONSE_DEGRADED,
    ERROR_RESPONSE_NOT_FOUND,
    ERROR_RESPONSE_VALIDATION,
    make_user,
    make_user_list,
    make_paginated_response,
)

__all__ = [
    # Данные
    "SAMPLE_USERS",
    "HEALTH_RESPONSE_OK",
    "HEALTH_RESPONSE_DEGRADED",
    "ERROR_RESPONSE_NOT_FOUND",
    "ERROR_RESPONSE_VALIDATION",
    # Фабрики
    "make_user",
    "make_user_list",
    "make_paginated_response",
]
