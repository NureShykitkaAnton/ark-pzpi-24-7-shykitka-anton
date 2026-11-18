"""Репозиторій доступу до таблиці місячних бюджетів."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.budgets.models import Budget
from app.modules.lines.models import PowerLine


class BudgetRepository(BaseRepository[Budget]):
    """Клас репозиторію для управління фінансовими лімітами."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Budget, session)

    async def get_by_line_and_period(
        self, power_line_id: uuid.UUID, year: int, month: int
    ) -> Budget | None:
        """Шукає бюджет для вказаної лінії за конкретний рік і місяць."""
        query = select(Budget).where(
            Budget.power_line_id == power_line_id,
            Budget.year == year,
            Budget.month == month,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> Sequence[Budget]:
        """Повертає список бюджетів усіх ліній користувача з можливістю фільтрації."""
        query = (
            select(Budget)
            .join(PowerLine, Budget.power_line_id == PowerLine.id)
            .where(PowerLine.user_id == user_id)
        )
        if power_line_id is not None:
            query = query.where(Budget.power_line_id == power_line_id)
        if year is not None:
            query = query.where(Budget.year == year)
        if month is not None:
            query = query.where(Budget.month == month)

        query = query.order_by(Budget.year.desc(), Budget.month.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
