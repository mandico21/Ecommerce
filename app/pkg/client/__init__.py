"""Базовые клиенты для работы с внешними API."""

from app.pkg.client.base import BaseApiClient, HttpMethod, HttpResult

__all__ = ["BaseApiClient", "HttpResult", "HttpMethod"]
