"""Репозиторій доступу до таблиці аномальних подій."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.anomalies.enums import AnomalyType
from app.modules.anomalies.models import AnomalyEvent
from app.modules.lines.models import PowerLine


class AnomalyRepository(BaseRepository[AnomalyEvent]):
    """Клас репозиторію для пошуку та оновлення аномалій споживання."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AnomalyEvent, session)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID | None = None,
        anomaly_type: AnomalyType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AnomalyEvent]:
        """Повертає список аномалій усіх ліній користувача у зворотному хронологічному порядку."""
        query = (
            select(AnomalyEvent)
            .join(PowerLine, AnomalyEvent.power_line_id == PowerLine.id)
            .where(PowerLine.user_id == user_id)
        )
        if power_line_id is not None:
            query = query.where(AnomalyEvent.power_line_id == power_line_id)
        if anomaly_type is not None:
            query = query.where(AnomalyEvent.anomaly_type == anomaly_type)

        query = (
            query.order_by(AnomalyEvent.detected_at.desc()).offset(skip).limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
