"""REST API маршрутизатор для управління push-токенами (FCM/APNs) та сповіщеннями."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import MessageResponse
from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_user
from app.modules.notifications.dependencies import get_notification_service
from app.modules.notifications.schemas import (
    NotificationRead,
    PushTokenCreate,
    PushTokenRead,
)
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/push-tokens",
    response_model=PushTokenRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_push_token(
    data: PushTokenCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> PushTokenRead:
    """Реєструє або оновлює токен мобільного пристрою для отримання push-сповіщень."""
    token = await service.register_push_token(current_user.id, data)
    return PushTokenRead.model_validate(token)


@router.get("/push-tokens", response_model=list[PushTokenRead])
async def list_push_tokens(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> list[PushTokenRead]:
    """Повертає список активних push-токенів поточного користувача."""
    tokens = await service.list_push_tokens(current_user.id)
    return [PushTokenRead.model_validate(t) for t in tokens]


@router.delete(
    "/push-tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_push_token(
    token_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> None:
    """Видаляє push-токен пристрою."""
    await service.delete_push_token(token_id, current_user.id)


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    unread_only: bool = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[NotificationRead]:
    """Повертає журнал системних сповіщень поточного користувача."""
    items = await service.list_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return [NotificationRead.model_validate(n) for n in items]


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationRead:
    """Позначає конкретне сповіщення як прочитане."""
    item = await service.mark_as_read(notification_id, current_user.id)
    return NotificationRead.model_validate(item)


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> MessageResponse:
    """Позначає всі непрочитані сповіщення користувача як прочитані."""
    updated_count = await service.mark_all_as_read(current_user.id)
    return MessageResponse(message=f"Marked {updated_count} notifications as read")
