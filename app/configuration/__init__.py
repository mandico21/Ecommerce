"""Конфигурация приложения."""

from app.configuration.providers import (
    ClientProvider,
    ConnectorsProvider,
    RepositoryProvider,
    ServiceProvider,
    SettingsProvider,
)

__all__ = [
    "SettingsProvider",
    "ConnectorsProvider",
    "RepositoryProvider",
    "ServiceProvider",
    "ClientProvider",
]
