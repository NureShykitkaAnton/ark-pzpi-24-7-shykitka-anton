"""Сервісний шар управління місячними бюджетами та фінансовим прогнозуванням."""

import calendar
import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.budgets.models import Budget
from app.modules.budgets.repository import BudgetRepository
from app.modules.budgets.schemas import BudgetCreate, BudgetUpdate
from app.modules.lines.service import PowerLineService


class BudgetService:
    """Сервіс бізнес-логіки контролю місячних бюджетів споживання."""

    def __init__(self, repo: BudgetRepository, line_service: PowerLineService) -> None:
        self.repo = repo
        self.line_service = line_service

    async def create_budget(self, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
        """Встановлює місячний бюджет для обраної лінії живлення."""
        await self.line_service.get_user_line(data.power_line_id, user_id)
        existing = await self.repo.get_by_line_and_period(
            data.power_line_id, data.year, data.month
        )
        if existing:
            raise ConflictException(
                f"Budget for {data.year}-{data.month:02d} already exists on this line"
            )
        return await self.repo.create(**data.model_dump())

    async def list_budgets(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> Sequence[Budget]:
        """Повертає список бюджетів користувача."""
        return await self.repo.get_by_user(
            user_id=user_id,
            power_line_id=power_line_id,
            year=year,
            month=month,
        )

    async def get_user_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget:
        """Отримує бюджет за UUID і перевіряє право доступу."""
        budget = await self.repo.get_by_id(budget_id)
        if not budget:
            raise NotFoundException("Budget not found")
        await self.line_service.get_user_line(budget.power_line_id, user_id)
        return budget

    async def update_budget(
        self, budget_id: uuid.UUID, user_id: uuid.UUID, data: BudgetUpdate
    ) -> Budget:
        """Оновлює суму ліміту або поріг попередження бюджету."""
        budget = await self.get_user_budget(budget_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(budget, **update_data)

    async def delete_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Видаляє місячний бюджетний ліміт."""
        budget = await self.get_user_budget(budget_id, user_id)
        await self.repo.delete(budget)

    async def register_consumption(
        self,
        power_line_id: uuid.UUID,
        recorded_at: datetime,
        energy_delta_kwh: Decimal,
        cost_delta: Decimal,
    ) -> Budget | None:
        """Оновлює накопичені витрати, прогноз до кінця місяця та прапорці сповіщень (80% / 100%)."""
        budget = await self.repo.get_by_line_and_period(
            power_line_id, recorded_at.year, recorded_at.month
        )
        if not budget:
            return None

        new_kwh = (budget.consumed_kwh + energy_delta_kwh).quantize(Decimal("0.0001"))
        new_cost = (budget.accumulated_cost + cost_delta).quantize(Decimal("0.01"))

        days_in_month = calendar.monthrange(recorded_at.year, recorded_at.month)[1]
        elapsed_days = max(1, recorded_at.day)
        forecasted = (
            (new_cost / Decimal(elapsed_days)) * Decimal(days_in_month)
        ).quantize(Decimal("0.01"))

        utilization_pct = (
            (new_cost / budget.limit_amount) * Decimal(100)
            if budget.limit_amount > 0
            else Decimal(0)
        )
        warn_notified = budget.warn_notified or (
            utilization_pct >= budget.warn_threshold_pct
        )
        limit_notified = budget.limit_notified or (utilization_pct >= Decimal("100.00"))

        return await self.repo.update(
            budget,
            consumed_kwh=new_kwh,
            accumulated_cost=new_cost,
            forecasted_cost=forecasted,
            warn_notified=warn_notified,
            limit_notified=limit_notified,
        )
