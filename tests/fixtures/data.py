"""Фикстуры с тестовыми данными."""

from datetime import datetime, timezone
from uuid import uuid4


# ═══════════════════════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_USERS = [
    {
        "id": str(uuid4()),
        "email": "john@example.com",
        "name": "John Doe",
        "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": str(uuid4()),
        "email": "jane@example.com",
        "name": "Jane Smith",
        "created_at": datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": str(uuid4()),
        "email": "bob@example.com",
        "name": "Bob Wilson",
        "created_at": datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# API Responses
# ═══════════════════════════════════════════════════════════════════════════════

HEALTH_RESPONSE_OK = {
    "status": "ok",
}

HEALTH_RESPONSE_DEGRADED = {
    "status": "degraded",
    "checks": {
        "postgres": False,
    },
}

ERROR_RESPONSE_NOT_FOUND = {
    "message": "Запись не найдена",
    "details": None,
    "request_id": None,
}

ERROR_RESPONSE_VALIDATION = {
    "message": "Ошибка валидации",
    "details": {"field": "email", "error": "invalid format"},
    "request_id": None,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Factories
# ═══════════════════════════════════════════════════════════════════════════════

def make_user(
    id: str | None = None,
    email: str = "test@example.com",
    name: str = "Test User",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> dict:
    """
    Фабрика для создания тестового пользователя.

    Использование:
        user = make_user(email="custom@example.com")
        user_with_id = make_user(id="550e8400-e29b-41d4-a716-446655440000")
    """
    now = datetime.now(timezone.utc)
    return {
        "id": id or str(uuid4()),
        "email": email,
        "name": name,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }


def make_user_list(count: int = 3) -> list[dict]:
    """
    Фабрика для создания списка тестовых пользователей.

    Использование:
        users = make_user_list(5)
    """
    return [
        make_user(email=f"user{i}@example.com", name=f"User {i}")
        for i in range(1, count + 1)
    ]


def make_paginated_response(
    items: list[dict],
    total: int,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Фабрика для создания пагинированного ответа.

    Использование:
        response = make_paginated_response(users, total=100, page=2)
    """
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
