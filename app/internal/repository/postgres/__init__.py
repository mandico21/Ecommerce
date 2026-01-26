"""PostgreSQL репозитории."""

from app.internal.repository.postgres.mapping import collect_response
from app.internal.repository.postgres.user import UserRepository

__all__ = ["UserRepository", "collect_response"]
