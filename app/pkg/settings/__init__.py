"""Global point to cached settings."""

from app.pkg.settings.settings import APISettings, PostgresSettings, Settings, get_settings

__all__ = ["Settings", "get_settings", "settings", "PostgresSettings", "APISettings"]

settings: Settings = get_settings()
