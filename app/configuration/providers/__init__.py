"""Dishka DI провайдеры для слоёв приложения."""

from app.configuration.providers.client import ClientProvider
from app.configuration.providers.connectors import ConnectorsProvider
from app.configuration.providers.repository import RepositoryProvider
from app.configuration.providers.request_context import RequestContextProvider
from app.configuration.providers.service import ServiceProvider
from app.configuration.providers.settings import SettingsProvider

__all__ = [
    "SettingsProvider",
    "ConnectorsProvider",
    "RepositoryProvider",
    "ServiceProvider",
    "ClientProvider",
    "RequestContextProvider",
]
