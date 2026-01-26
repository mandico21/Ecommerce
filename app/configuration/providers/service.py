"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider

# from dishka import Provider, Scope, provide
# from app.internal.service.user import UserService
# from app.internal.repository.postgres import UserRepository


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""

    # Пример:
    # @provide(scope=Scope.REQUEST)
    # def user_service(self, user_repo: UserRepository) -> UserService:
    #     return UserService(user_repo)
    pass
