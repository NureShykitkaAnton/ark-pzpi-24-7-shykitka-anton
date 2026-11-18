"""Репозиторій доступу до часових рядів телеметрії та профілів навантаження."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.lines.models import PowerLine
from app.modules.telemetry.models import LoadProfile, TelemetryReading


class TelemetryRepository(BaseRepository[TelemetryReading]):
    """Клас репозиторію для високошвидкісного запису та вибірки часових рядів."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TelemetryReading, session)

    async def get_latest_for_line(
        self, power_line_id: uuid.UUID
    ) -> TelemetryReading | None:
        """Повертає останній за часом вимір для вказаної лінії живлення."""
        query = (
            select(TelemetryReading)
            .where(TelemetryReading.power_line_id == power_line_id)
            .order_by(TelemetryReading.recorded_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_range_for_line(
        self,
        power_line_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 500,
    ) -> Sequence[TelemetryReading]:
        """Вибирає впорядкований часовий ряд відліків за інтервал часу."""
        query = select(TelemetryReading).where(
            TelemetryReading.power_line_id == power_line_id
        )
        if start_time is not None:
            query = query.where(TelemetryReading.recorded_at >= start_time)
        if end_time is not None:
            query = query.where(TelemetryReading.recorded_at <= end_time)

        query = query.order_by(TelemetryReading.recorded_at.asc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()


class LoadProfileRepository(BaseRepository[LoadProfile]):
    """Клас репозиторію для збережених профілів навантаження."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(LoadProfile, session)

    async def get_by_user(
        self, user_id: uuid.UUID, power_line_id: uuid.UUID | None = None
    ) -> Sequence[LoadProfile]:
        """Повертає збережені профілі навантаження для ліній користувача."""
        query = (
            select(LoadProfile)
            .join(PowerLine, LoadProfile.power_line_id == PowerLine.id)
            .where(PowerLine.user_id == user_id)
        )
        if power_line_id is not None:
            query = query.where(LoadProfile.power_line_id == power_line_id)
        query = query.order_by(LoadProfile.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
