"""Unit тесты для безопасного логирования BaseApiClient."""

import pytest

from app.pkg.client.base import _fmt_url


@pytest.mark.unit
class TestBaseApiClientHelpers:
    def test_fmt_url_masks_sensitive_query_params(self):
        url = _fmt_url(
            "/callback",
            {
                "token": "secret-token",
                "page": 2,
                "api_key": "abc123",
            },
        )

        assert "token=%2A%2A%2A" in url
        assert "api_key=%2A%2A%2A" in url
        assert "page=2" in url
        assert "secret-token" not in url
        assert "abc123" not in url

