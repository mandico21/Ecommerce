from http import HTTPStatus

from app.pkg.models.base import AppError


class JWTError(AppError):
    http_status = HTTPStatus.UNAUTHORIZED
    message = "Unauthorized"
