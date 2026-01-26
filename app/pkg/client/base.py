__all__ = ["BaseApiClient", "HttpResult", "HttpMethod"]

import abc
import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, ClassVar, Literal, Mapping
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout, ClientResponse, TCPConnector
from aiohttp.client_exceptions import ClientError
from pydantic import AnyUrl

from app.pkg.logger import get_logger

log = get_logger("app.http.client")

# Типы HTTP методов
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]


@dataclass(slots=True)
class HttpResult:
    """Результат HTTP запроса с метаданными."""
    status: int | None
    headers: Mapping[str, str]
    body: bytes
    duration_ms: int
    error: str | None = None
    error_type: str | None = None
    attempt: int = 1

    def ok(self) -> bool:
        """Проверка успешности запроса (2xx статус)."""
        return self.status is not None and 200 <= self.status < 300

    def text(self, encoding: str = "utf-8", errors: str = "ignore") -> str:
        """Декодировать тело ответа в строку."""
        try:
            return self.body.decode(encoding, errors=errors)
        except Exception:
            return ""

    def json(self) -> Any | None:
        """Распарсить тело ответа как JSON."""
        try:
            import json
            return json.loads(self.text())
        except Exception:
            return None


# ── Вспомогательные функции ──────────────────────────────────────────────

_SENSITIVE = {"authorization", "x-api-key", "proxy-authorization", "x-auth-token", "api-key"}


def _mask_value_partial(value: str, head: int = 4, tail: int = 4) -> str:
    """Маскировать значение, оставляя первые и последние символы."""
    n = len(value)
    if n <= 2:
        return "*" * n
    if n <= head + tail:
        # Оставляем первый и последний символ
        return value[0] + "*" * (n - 2) + value[-1]
    return value[:head] + "*" * (n - head - tail) + value[-tail:]


def _mask_auth_value(v: str) -> str:
    """Маскировать значение авторизации (Bearer, Token, Basic)."""
    for p in ("Bearer ", "Token ", "Basic "):
        if v.startswith(p):
            core = v[len(p):]
            return p + _mask_value_partial(core)
    return _mask_value_partial(v)


def _mask_headers(h: Mapping[str, str] | None) -> dict[str, str]:
    """Маскировать чувствительные заголовки для безопасного логирования."""
    if not h:
        return {}
    out: dict[str, str] = {}
    for k, v in h.items():
        if k.lower() in _SENSITIVE:
            out[k] = _mask_auth_value(str(v))
        else:
            out[k] = str(v)
    return out


def _fmt_url(path: str, params: Mapping[str, Any] | None) -> str:
    """Форматировать URL с query параметрами для логирования."""
    if not params:
        return path
    try:
        qs = urlencode(params, doseq=True)
        sep = "&" if "?" in path else "?"
        return f"{path}{sep}{qs}"
    except Exception:
        return path


def _compact_preview(body: bytes, limit: int) -> str:
    """Создать компактное превью тела ответа для логирования."""
    if not body:
        return ""
    snippet = body[:limit]
    # Сначала пробуем JSON
    try:
        import json
        obj = json.loads(snippet.decode("utf-8"))
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass
    # Затем текст
    try:
        return snippet.decode("utf-8", errors="ignore")
    except Exception:
        return "<binary>"


# ── Базовый клиент ────────────────────────────────────────────────────────

class BaseApiClient(abc.ABC):
    """
    Абстрактный отказоустойчивый HTTP-клиент на aiohttp.

    Особенности:
    - Не бросает исключения, всегда возвращает HttpResult
    - Маскирует чувствительные заголовки в логах
    - Структурированное логирование с метриками времени
    - Точки расширения для кастомизации (prepare_request, postprocess, default_headers)
    """

    client_name: ClassVar[str]
    base_url: ClassVar[str | None] = None  # Можно задать в наследнике

    def __init__(
        self,
        base_url: AnyUrl | str | None = None,
        timeout: float = 30.0,
        headers: Mapping[str, str] | None = None,
        connector: TCPConnector | None = None,
        log_bodies: bool = False,
        log_body_limit: int = 600,
        session: ClientSession | None = None,
    ) -> None:
        if not getattr(self, "client_name", None):
            raise TypeError(f"{type(self).__name__}.client_name должен быть установлен")

        resolved = str(base_url or type(self).base_url or "")
        if not resolved:
            raise ValueError(
                f"{type(self).__name__}: base_url обязателен (аргумент или class base_url)"
            )

        self._own_session = session is None
        self._session = session or ClientSession(
            base_url=resolved,
            timeout=ClientTimeout(total=timeout),
            headers=dict(headers or {}),
            connector=connector,
        )
        self._base_url = resolved
        self._log_bodies = log_bodies
        self._log_body_limit = log_body_limit

    # Точки расширения
    def default_headers(self) -> Mapping[str, str]:
        """Возвращает заголовки по умолчанию (например, Authorization)."""
        return {}

    def prepare_request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
        json: Any | None,
        data: Any | None,
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, str] | None, Any | None, Any | None]:
        """
        Подготовка запроса перед отправкой.
        Можно модифицировать params, headers, json, data.
        Полезно для добавления trace-id, идемпотентности и т.д.
        """
        h = dict(self.default_headers())
        if headers:
            h.update(headers)
        return params, h, json, data

    def postprocess(self, result: HttpResult) -> HttpResult:
        """
        Постобработка результата.
        Можно нормализовать специфичные коды (например, 409 → успех).
        """
        return result

    # Управление жизненным циклом
    async def close(self) -> None:
        """Закрыть HTTP сессию."""
        if self._own_session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "BaseApiClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # Основной метод запроса
    async def request(
        self,
        method: HttpMethod,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        **kwargs: Any,
    ) -> HttpResult:
        """
        Выполнить HTTP запрос.

        Возвращает:
            HttpResult с status, headers, body, duration_ms.
            При ошибках status=None, error заполнен описанием.
        """
        params, headers, json, data = self.prepare_request(
            method, path, params=params, headers=headers, json=json, data=data
        )

        display_url = _fmt_url(path, params)
        masked_headers = _mask_headers(headers)

        t0 = perf_counter()
        log.info(
            "[%s] [request]: <%s> %s %s",
            self.client_name, method, display_url,
            {"headers": masked_headers} if masked_headers else {},
        )

        try:
            resp: ClientResponse = await self._session.request(
                method, path, params=params, headers=headers, json=json, data=data, **kwargs
            )
            status = resp.status
            raw_headers = {k: v for k, v in resp.headers.items()}
            body = await resp.read()
            dt = int((perf_counter() - t0) * 1000)

            if self._log_bodies:
                body_preview = _compact_preview(body, self._log_body_limit)
                log.info(
                    "[%s] [response]: <%s> %s %dмс %s",
                    self.client_name, status, display_url, dt, body_preview,
                )
            else:
                log.info(
                    "[%s] [response]: <%s> %s %dмс %dБ",
                    self.client_name, status, display_url, dt, len(body),
                )

            await resp.release()
            return self.postprocess(
                HttpResult(status=status, headers=raw_headers, body=body, duration_ms=dt, attempt=1)
            )

        except asyncio.TimeoutError as e:
            dt = int((perf_counter() - t0) * 1000)
            log.warning(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс таймаут",
                self.client_name, type(e).__name__, display_url, dt,
            )
            return self.postprocess(
                HttpResult(
                    status=None, headers={}, body=b"", duration_ms=dt,
                    error="timeout", error_type=type(e).__name__, attempt=1
                )
            )
        except ClientError as e:
            dt = int((perf_counter() - t0) * 1000)
            log.warning(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс %s",
                self.client_name, type(e).__name__, display_url, dt, str(e),
            )
            return self.postprocess(
                HttpResult(
                    status=None, headers={}, body=b"", duration_ms=dt,
                    error=str(e), error_type=type(e).__name__, attempt=1
                )
            )
        except Exception as e:
            dt = int((perf_counter() - t0) * 1000)
            log.error(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс %r",
                self.client_name, type(e).__name__, display_url, dt, e,
            )
            return self.postprocess(
                HttpResult(
                    status=None, headers={}, body=b"", duration_ms=dt,
                    error=str(e), error_type=type(e).__name__, attempt=1
                )
            )

    # Вспомогательные методы для HTTP методов
    async def get(self, path: str, **kwargs: Any) -> HttpResult:
        """Выполнить GET запрос."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> HttpResult:
        """Выполнить POST запрос."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> HttpResult:
        """Выполнить PUT запрос."""
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> HttpResult:
        """Выполнить PATCH запрос."""
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> HttpResult:
        """Выполнить DELETE запрос."""
        return await self.request("DELETE", path, **kwargs)


"""
Документация BaseApiClient
--------------------------------
Назначение:
    Абстрактный HTTP-клиент на aiohttp, не бросает исключений и всегда
    возвращает HttpResult. Логи «читаемые» (метод, URL, время, размер/превью),
    чувствительные заголовки маскируются (Authorization: первые 4 и последние 4).

Как создать клиент (наследник):
  1) Унаследуйтесь и задайте class атрибуты:
        client_name = "Человеко-читаемое имя клиента в логах"
        base_url = "https://api.example.com"   # можно не задавать и передавать в __init__
  
  2) При необходимости переопределите:
        - default_headers()      — добавить общие заголовки (например, Authorization)
        - prepare_request(...)   — модифицировать params/headers/json/data (идемпотентность, trace-id)
        - postprocess(result)    — нормализовать результат (напр., 409 → успех)
  
  3) Определите методы-обёртки под эндпоинты и используйте get/post/put/patch/delete.

Минимальный пример:
    from typing import Mapping
    from pydantic import SecretStr
    from app.pkg.client.base import BaseApiClient, HttpResult

    class PaymentGatewayClient(BaseApiClient):
        client_name = "Payment"
        base_url = "https://pay.example.com"

        def __init__(self, *, access_token: SecretStr, **kwargs):
            self._token = access_token
            super().__init__(**kwargs)

        def default_headers(self) -> Mapping[str, str]:
            return {"Authorization": f"Token {self._token.get_secret_value()}"}

        async def get_payment(self, *, payment_id: int) -> HttpResult:
            return await self.get(f"/api/v2/payments/admin/id/{payment_id}/")

Использование:
    from pydantic import SecretStr

    async def demo():
        async with PaymentGatewayClient(
            access_token=SecretStr("secret-token"),
            timeout=10.0,
            log_bodies=True,          # логировать компактное превью тела (до log_body_limit)
        ) as client:
            res = await client.get_payment(payment_id=123)
            if res.ok():
                data = res.json() or {}
            else:
                # res.status может быть None при таймауте/сетевой ошибке
                print("ошибка:", res.status, res.error, res.text()[:200])

Интеграция с Dishka DI:
    from typing import AsyncIterator
    from dishka import Provider, Scope, provide
    from contextlib import asynccontextmanager

    class ClientProvider(Provider):
        @provide(scope=Scope.APP)
        @asynccontextmanager
        async def payment_gateway(self, settings: Settings) -> AsyncIterator[PaymentGatewayClient]:
            client = PaymentGatewayClient(
                access_token=SecretStr(settings.PAYMENTS.ACCESS_TOKEN),
                base_url=settings.PAYMENTS.URL,
                timeout=settings.PAYMENTS.TIMEOUT,
                log_bodies=False,
            )
            try:
                yield client
            finally:
                await client.close()

Возвращаемое значение HttpResult:
    - status: int | None      (2xx → ok(); None при таймауте/сетевой ошибке)
    - headers: Mapping[str, str]
    - body: bytes             (helpers: .text(), .json())
    - duration_ms: int
    - error / error_type: str | None (заполнены при ошибках)

Примечания:
    - base_url можно задать в классе или передать в __init__.
    - Клиент управляет сессией сам (async with / close()) — без __del__.
    - Для единичного запроса используйте client.get/post/...; исключения наружу не летят.
    - Все логи структурированные, чувствительные данные автоматически маскируются.
"""
