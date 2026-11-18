"""Репозиторій доступу до таблиці тарифних планів."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.tariffs.models import Tariff


class TariffRepository(BaseRepository[Tariff]):
    """Клас репозиторію для управління тарифами користувача."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Tariff, session)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Tariff]:
        """Повертає всі тарифні плани вказаного користувача."""
        query = (
            select(Tariff)
            .where(Tariff.user_id == user_id)
            .order_by(Tariff.is_default.desc(), Tariff.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def unset_default_for_user(self, user_id: uuid.UUID) -> None:
        """Скидає ознаку тарифу за замовчуванням для всіх тарифів користувача."""
        query = update(Tariff).where(Tariff.user_id == user_id).values(is_default=False)
        await self.session.execute(query)
        await self.session.flush()
