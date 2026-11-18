"""REST API маршрутизатор для управління профілями та користувачами."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.config import settings
from app.core.schemas import MessageResponse
from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_superuser, get_current_user
from app.modules.users.dependencies import get_user_service
from app.modules.users.models import User
from app.modules.users.schemas import (
    PasswordChangeRequest,
    UserAdminUpdate,
    UserRead,
    UserUpdate,
)
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    """Повертає профіль поточного авторизованого користувача."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_current_user_profile(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Оновлює персональні дані, мову інтерфейсу, часову зону або систему мір."""
    updated = await user_service.update_profile(current_user, data)
    return UserRead.model_validate(updated)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Змінює пароль поточного користувача."""
    await user_service.change_password(current_user, data.new_password)
    return MessageResponse(message="Password successfully updated")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Виконує видалення власного облікового запису з очищенням персональних даних."""
    await user_service.delete(current_user)
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(get_current_superuser)],
)
async def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[UserRead]:
    """Повертає список усіх користувачів системи (доступно адміністратору)."""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [UserRead.model_validate(u) for u in users]


@router.patch(
    "/{user_id}/status",
    response_model=UserRead,
    dependencies=[Depends(get_current_superuser)],
)
async def admin_update_user_status(
    user_id: UUID7,
    data: UserAdminUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Змінює статус, роль або рівень підписки користувача (доступно адміністратору)."""
    user = await user_service.get_by_id(user_id)
    updated = await user_service.admin_update_user(user, data)
    return UserRead.model_validate(updated)
