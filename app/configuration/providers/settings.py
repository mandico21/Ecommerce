"""Провайдер настроек для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.pkg.settings import Settings, get_settings


class SettingsProvider(Provider):
    """Предоставляет настройки приложения как синглтон."""

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return get_settings()
