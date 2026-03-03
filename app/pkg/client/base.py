"""Базовый HTTP-клиент на httpx (async, connection pooling, timeouts)."""

from __future__ import annotations

__all__ = ["BaseApiClient", "HttpResult", "HttpMethod"]

import abc
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, ClassVar, Literal, Mapping

import httpx
from pydantic import AnyUrl

from app.pkg.logger import get_logger

log = get_logger("app.http.client")

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
            return json.loads(self.text())
        except Exception:
            return None


# ── Вспомогательные функции ──────────────────────────────────────────────

_SENSITIVE = {"authorization", "x-api-key", "proxy-authorization", "x-auth-token", "api-key"}
_SENSITIVE_QUERY_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "key",
    "signature",
    "sig",
    "password",
    "secret",
}


def _mask_value_partial(value: str, head: int = 4, tail: int = 4) -> str:
    """Маскировать значение, оставляя первые и последние символы."""
    n = len(value)
    if n <= 2:
        return "*" * n
    if n <= head + tail:
        return value[0] + "*" * (n - 2) + value[-1]
    return value[:head] + "*" * (n - head - tail) + value[-tail:]


def _mask_auth_value(v: str) -> str:
    """Маскировать значение авторизации (Bearer, Token, Basic)."""
    for p in ("Bearer ", "Token ", "Basic "):
        if v.startswith(p):
            core = v[len(p) :]
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
        from urllib.parse import urlencode

        masked_params: dict[str, Any] = {}
        for key, value in params.items():
            if key.lower() in _SENSITIVE_QUERY_KEYS:
                masked_params[key] = "***"
            else:
                masked_params[key] = value

        qs = urlencode(masked_params, doseq=True)
        sep = "&" if "?" in path else "?"
        return f"{path}{sep}{qs}"
    except Exception:
        return path


def _compact_preview(body: bytes, limit: int) -> str:
    """Создать компактное превью тела ответа для логирования."""
    if not body:
        return ""
    snippet = body[:limit]
    try:
        obj = json.loads(snippet.decode("utf-8"))
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass
    try:
        return snippet.decode("utf-8", errors="ignore")
    except Exception:
        return "<binary>"


# ── Базовый клиент ────────────────────────────────────────────────────────


class BaseApiClient(abc.ABC):
    """
    Абстрактный отказоустойчивый HTTP-клиент на httpx.

    Особенности:
    - Не бросает исключения, всегда возвращает HttpResult
    - Маскирует чувствительные заголовки в логах
    - Структурированное логирование с метриками времени
    - Connection pooling и лимиты через httpx.Limits
    - Точки расширения: prepare_request, postprocess, default_headers
    """

    client_name: ClassVar[str]
    base_url: ClassVar[str | None] = None

    def __init__(
        self,
        base_url: AnyUrl | str | None = None,
        timeout: float = 30.0,
        headers: Mapping[str, str] | None = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        log_bodies: bool = False,
        log_body_limit: int = 600,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not getattr(self, "client_name", None):
            raise TypeError(f"{type(self).__name__}.client_name должен быть установлен")

        resolved = str(base_url or type(self).base_url or "")
        if not resolved:
            raise ValueError(
                f"{type(self).__name__}: base_url обязателен (аргумент или class base_url)"
            )

        self._own_client = client is None
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client = client or httpx.AsyncClient(
            base_url=resolved,
            timeout=httpx.Timeout(timeout),
            headers=dict(headers or {}),
            limits=limits,
        )
        self._base_url = resolved
        self._log_bodies = log_bodies
        self._log_body_limit = log_body_limit

    def default_headers(self) -> Mapping[str, str]:
        """Возвращает заголовки по умолчанию (например, Authorization)."""
        return {}

    def prepare_request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
        json_data: Any | None,
        content: Any | None,
    ) -> tuple[
        Mapping[str, Any] | None,
        Mapping[str, str] | None,
        Any | None,
        Any | None,
    ]:
        """
        Подготовка запроса перед отправкой.
        Можно модифицировать params, headers, json, content.
        """
        h = dict(self.default_headers())
        if headers:
            h.update(headers)
        return params, h, json_data, content

    def postprocess(self, result: HttpResult) -> HttpResult:
        """Постобработка результата (нормализация кодов и т.д.)."""
        return result

    async def close(self) -> None:
        """Закрыть HTTP-клиент и пул соединений."""
        if self._own_client:
            await self._client.aclose()

    async def __aenter__(self) -> "BaseApiClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def request(
        self,
        method: HttpMethod,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
        content: Any | None = None,
        **kwargs: Any,
    ) -> HttpResult:
        """
        Выполнить HTTP запрос.

        Возвращает HttpResult с status, headers, body, duration_ms.
        При ошибках status=None, error заполнен описанием.
        """
        params, headers, json_data, content = self.prepare_request(
            method, path, params=params, headers=headers, json_data=json, content=content
        )

        display_url = _fmt_url(path, params)
        masked_headers = _mask_headers(headers)

        t0 = perf_counter()
        log.info(
            "[%s] [request]: <%s> %s %s",
            self.client_name,
            method,
            display_url,
            {"headers": masked_headers} if masked_headers else {},
        )

        try:
            resp = await self._client.request(
                method,
                path,
                params=params,
                headers=headers,
                json=json_data,
                content=content,
                **kwargs,
            )
            status = resp.status_code
            raw_headers = dict(resp.headers)
            body = resp.content
            dt = int((perf_counter() - t0) * 1000)

            if self._log_bodies:
                body_preview = _compact_preview(body, self._log_body_limit)
                log.info(
                    "[%s] [response]: <%s> %s %dмс %s",
                    self.client_name,
                    status,
                    display_url,
                    dt,
                    body_preview,
                )
            else:
                log.info(
                    "[%s] [response]: <%s> %s %dмс %dБ",
                    self.client_name,
                    status,
                    display_url,
                    dt,
                    len(body),
                )

            return self.postprocess(
                HttpResult(
                    status=status,
                    headers=raw_headers,
                    body=body,
                    duration_ms=dt,
                    attempt=1,
                )
            )

        except httpx.TimeoutException as e:
            dt = int((perf_counter() - t0) * 1000)
            log.warning(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс таймаут",
                self.client_name,
                type(e).__name__,
                display_url,
                dt,
            )
            return self.postprocess(
                HttpResult(
                    status=None,
                    headers={},
                    body=b"",
                    duration_ms=dt,
                    error="timeout",
                    error_type=type(e).__name__,
                    attempt=1,
                )
            )
        except httpx.HTTPError as e:
            dt = int((perf_counter() - t0) * 1000)
            log.warning(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс %s",
                self.client_name,
                type(e).__name__,
                display_url,
                dt,
                str(e),
            )
            return self.postprocess(
                HttpResult(
                    status=None,
                    headers={},
                    body=b"",
                    duration_ms=dt,
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=1,
                )
            )
        except Exception as e:
            dt = int((perf_counter() - t0) * 1000)
            log.error(
                "[%s] [response]: <ОШИБКА:%s> %s %dмс %r",
                self.client_name,
                type(e).__name__,
                display_url,
                dt,
                e,
            )
            return self.postprocess(
                HttpResult(
                    status=None,
                    headers={},
                    body=b"",
                    duration_ms=dt,
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=1,
                )
            )

    async def get(self, path: str, **kwargs: Any) -> HttpResult:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> HttpResult:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> HttpResult:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> HttpResult:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> HttpResult:
        return await self.request("DELETE", path, **kwargs)
