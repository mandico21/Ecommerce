"""Пример роутера для пользователей."""

from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from fastapi import APIRouter, HTTPException, Query, status

from app.internal.models.user.response import UserListResponse, UserResponse
from app.internal.repository.postgres import UserRepository
from app.pkg.models.base import NotFoundError

router = APIRouter()


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Получить список пользователей",
    description="Возвращает пагинированный список пользователей",
)
async def list_users(
    user_repo: Annotated[UserRepository, FromDishka()],
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
) -> UserListResponse:
    """Получить список пользователей с пагинацией."""
    result = await user_repo.list_paginated(page=page, page_size=page_size)

    return UserListResponse(
        items=[UserResponse(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        pages=result["pages"],
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя по ID",
    description="Возвращает детальную информацию о пользователе",
    responses={
        404: {"description": "Пользователь не найден"},
    },
)
async def get_user(
    user_id: UUID,
    user_repo: Annotated[UserRepository, FromDishka()],
) -> UserResponse:
    """Получить пользователя по ID."""
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description="Создаёт нового пользователя",
)
async def create_user(
    email: str,
    name: str,
    user_repo: Annotated[UserRepository, FromDishka()],
) -> UserResponse:
    """Создать нового пользователя."""
    user = await user_repo.create(email=email, name=name)
    return UserResponse(**user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Удаляет пользователя по ID",
    responses={
        404: {"description": "Пользователь не найден"},
    },
)
async def delete_user(
    user_id: UUID,
    user_repo: Annotated[UserRepository, FromDishka()],
) -> None:
    """Удалить пользователя."""
    deleted = await user_repo.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
