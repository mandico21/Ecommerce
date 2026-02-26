"""Точка входа для запуска приложения с правильной конфигурацией логирования."""

import uvicorn

from app.pkg.logger.uvicorn_config import LOGGING_CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=LOGGING_CONFIG,
    )

