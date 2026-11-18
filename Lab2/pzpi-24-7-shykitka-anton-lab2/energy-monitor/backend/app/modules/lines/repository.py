"""Репозиторій доступу до таблиці ліній живлення у СУБД PostgreSQL."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repositories import BaseRepository
from app.modules.lines.models import PowerLine


class PowerLineRepository(BaseRepository[PowerLine]):
    """Клас репозиторію для управління лініями електроживлення."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PowerLine, session)

    async def get_by_id_with_tariff(self, line_id: uuid.UUID) -> PowerLine | None:
        """Повертає лінію живлення разом із підвантаженим об'єктом тарифу."""
        query = (
            select(PowerLine)
            .options(selectinload(PowerLine.tariff))
            .where(PowerLine.id == line_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_device_uid(self, device_uid: str) -> PowerLine | None:
        """Шукає лінію живлення за апаратним ідентифікатором ESP32."""
        query = select(PowerLine).where(
            PowerLine.device_uid == device_uid.strip().upper()
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> PowerLine | None:
        """Шукає лінію живлення за SHA-256 хешем API-токена пристрою."""
        query = (
            select(PowerLine)
            .options(selectinload(PowerLine.tariff))
            .where(PowerLine.device_token_hash == token_hash)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[PowerLine]:
        """Повертає список усіх ліній живлення конкретного користувача."""
        query = (
            select(PowerLine)
            .where(PowerLine.user_id == user_id)
            .order_by(PowerLine.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
