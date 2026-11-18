"""Сервіс реєстрації push-токенів мобільних клієнтів та управління сповіщеннями."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.models import Notification, PushToken
from app.modules.notifications.repository import (
    NotificationRepository,
    PushTokenRepository,
)
from app.modules.notifications.schemas import PushTokenCreate


class NotificationService:
    """Сервіс доставки та управління ранніми попередженнями і push-сповіщеннями."""

    def __init__(
        self,
        token_repo: PushTokenRepository,
        notification_repo: NotificationRepository,
    ) -> None:
        self.token_repo = token_repo
        self.notification_repo = notification_repo

    async def register_push_token(
        self, user_id: uuid.UUID, data: PushTokenCreate
    ) -> PushToken:
        """Реєструє або оновлює push-токен пристрою (FCM / APNs)."""
        existing = await self.token_repo.get_by_token(data.device_token.strip())
        if existing:
            return await self.token_repo.update(
                existing,
                user_id=user_id,
                platform=data.platform,
                device_name=data.device_name,
                is_active=True,
            )
        return await self.token_repo.create(
            user_id=user_id,
            platform=data.platform,
            device_token=data.device_token.strip(),
            device_name=data.device_name,
            is_active=True,
        )

    async def list_push_tokens(self, user_id: uuid.UUID) -> Sequence[PushToken]:
        """Повертає список активних push-токенів користувача."""
        return await self.token_repo.get_by_user(user_id)

    async def delete_push_token(self, token_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Видаляє зареєстрований push-токен пристрою."""
        token = await self.token_repo.get_by_id(token_id)
        if not token:
            raise NotFoundException("Push token not found")
        if token.user_id != user_id:
            raise ForbiddenException("Access to this push token is forbidden")
        await self.token_repo.delete(token)

    async def create_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        body: str,
        power_line_id: uuid.UUID | None = None,
    ) -> Notification:
        """Створює запис сповіщення для подальшого відображення та push-доставки."""
        return await self.notification_repo.create(
            user_id=user_id,
            power_line_id=power_line_id,
            notification_type=notification_type,
            title=title,
            body=body,
            is_read=False,
            sent_at=datetime.now(UTC),
        )

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Повертає історію сповіщень поточного користувача."""
        return await self.notification_repo.get_by_user(
            user_id=user_id,
            unread_only=unread_only,
            skip=skip,
            limit=limit,
        )

    async def mark_as_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification:
        """Позначає конкретне сповіщення як прочитане."""
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundException("Notification not found")
        if notification.user_id != user_id:
            raise ForbiddenException("Access to this notification is forbidden")
        return await self.notification_repo.update(notification, is_read=True)

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Позначає всі сповіщення користувача як прочитані."""
        return await self.notification_repo.mark_all_read(user_id)
