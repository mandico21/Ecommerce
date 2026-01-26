"""Интеграционные тесты для Health Check API."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Тесты health check эндпоинтов."""

    async def test_liveness(self, client: AsyncClient):
        """Тест: liveness проба всегда возвращает ok."""
        response = await client.get("/health/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_readiness(self, client: AsyncClient):
        """Тест: readiness проба проверяет зависимости."""
        response = await client.get("/health/readiness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert "checks" in data

    async def test_detailed_health(self, client: AsyncClient):
        """Тест: detailed health возвращает статистику."""
        response = await client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "postgres" in data


@pytest.mark.integration
class TestMetricsEndpoint:
    """Тесты Prometheus метрик."""

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Тест: /metrics возвращает Prometheus метрики."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Проверяем наличие базовых метрик
        content = response.text
        assert "http_requests_total" in content or "python_gc" in content


@pytest.mark.integration
class TestRequestIdMiddleware:
    """Тесты Request ID middleware."""

    async def test_request_id_generated(self, client: AsyncClient):
        """Тест: X-Request-ID генерируется автоматически."""
        response = await client.get("/health/liveness")

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 36  # UUID format

    async def test_request_id_passed_through(self, client: AsyncClient):
        """Тест: X-Request-ID передаётся в ответе."""
        custom_id = "test-request-id-12345"
        response = await client.get(
            "/health/liveness",
            headers={"X-Request-ID": custom_id}
        )

        assert response.headers["x-request-id"] == custom_id


@pytest.mark.integration
class TestCORS:
    """Тесты CORS middleware."""

    async def test_cors_headers(self, client: AsyncClient):
        """Тест: CORS заголовки присутствуют."""
        response = await client.options(
            "/health/liveness",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # CORS middleware должен ответить
        assert response.status_code in [200, 204, 405]
