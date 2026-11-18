"""Залежності FastAPI для модуля сповіщень та push-токенів."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.notifications.repository import (
    NotificationRepository,
    PushTokenRepository,
)
from app.modules.notifications.service import NotificationService


def get_push_token_repository(session: SessionDep) -> PushTokenRepository:
    """Фабрика репозиторію push-токенів."""
    return PushTokenRepository(session)


def get_notification_repository(session: SessionDep) -> NotificationRepository:
    """Фабрика репозиторію сповіщень."""
    return NotificationRepository(session)


def get_notification_service(
    token_repo: Annotated[PushTokenRepository, Depends(get_push_token_repository)],
    notification_repo: Annotated[
        NotificationRepository, Depends(get_notification_repository)
    ],
) -> NotificationService:
    """Фабрика сервісу сповіщень."""
    return NotificationService(
        token_repo=token_repo,
        notification_repo=notification_repo,
    )
