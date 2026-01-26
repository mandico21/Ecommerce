"""Провайдер внешних клиентов для DI контейнера."""

from __future__ import annotations

from dishka import Provider

# from typing import AsyncIterator
# from dishka import Provider, Scope, provide
# from app.pkg.client.some_api import SomeApiClient


class ClientProvider(Provider):
    """Предоставляет клиенты внешних API."""

    # Пример:
    # @provide(scope=Scope.APP)
    # async def some_api_client(self, settings: Settings) -> AsyncIterator[SomeApiClient]:
    #     client = SomeApiClient(settings.SOME_API)
    #     await client.startup()
    #     try:
    #         yield client
    #     finally:
    #         await client.shutdown()
    pass
