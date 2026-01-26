from __future__ import annotations

from typing import Any

from app.pkg.models.base import BaseModel


class ErrorPayload(BaseModel):
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None
