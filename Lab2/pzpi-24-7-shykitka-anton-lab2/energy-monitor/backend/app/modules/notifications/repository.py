"""Репозиторії для роботи з таблицями push_tokens та notifications."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.notifications.models import Notification, PushToken


class PushTokenRepository(BaseRepository[PushToken]):
    """Репозиторій управління push-токенами мобільних пристроїв."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PushToken, session)

    async def get_by_token(self, device_token: str) -> PushToken | None:
        """Шукає запис за рядком push-токена."""
        query = select(PushToken).where(PushToken.device_token == device_token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> Sequence[PushToken]:
        """Повертає всі активні push-токени користувача."""
        query = (
            select(PushToken)
            .where(PushToken.user_id == user_id, PushToken.is_active.is_(True))
            .order_by(PushToken.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class NotificationRepository(BaseRepository[Notification]):
    """Репозиторій доступу до журналу сповіщень користувача."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Повертає список сповіщень користувача у зворотному хронологічному порядку."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Позначає всі непрочитані сповіщення користувача як прочитані."""
        query = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount)
