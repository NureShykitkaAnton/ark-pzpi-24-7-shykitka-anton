"""Pydantic-схеми для створення, оновлення та читання бюджетних лімітів."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.types import UUID7


class BudgetCreate(BaseModel):
    """Схема створення місячного бюджету на лінію живлення."""

    power_line_id: UUID7
    year: int = Field(ge=2024, le=2100)
    month: int = Field(ge=1, le=12)
    limit_amount: Decimal = Field(gt=Decimal(0), max_digits=12, decimal_places=2)
    warn_threshold_pct: Decimal = Field(
        default=Decimal("80.00"),
        gt=Decimal(0),
        le=Decimal(100),
        max_digits=5,
        decimal_places=2,
    )


class BudgetUpdate(BaseModel):
    """Схема оновлення параметрів бюджетного ліміту."""

    limit_amount: Decimal | None = Field(
        default=None, gt=Decimal(0), max_digits=12, decimal_places=2
    )
    warn_threshold_pct: Decimal | None = Field(
        default=None,
        gt=Decimal(0),
        le=Decimal(100),
        max_digits=5,
        decimal_places=2,
    )


class BudgetRead(BaseModel):
    """Схема відображення стану виконання бюджету у відповідях REST API."""

    id: UUID7
    power_line_id: UUID7
    year: int
    month: int
    limit_amount: Decimal
    consumed_kwh: Decimal
    accumulated_cost: Decimal
    forecasted_cost: Decimal
    warn_threshold_pct: Decimal
    warn_notified: bool
    limit_notified: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utilization_pct(self) -> Decimal:
        """Обчислює поточний відсоток використання встановленого місячного бюджету."""
        if self.limit_amount <= 0:
            return Decimal("0.00")
        return ((self.accumulated_cost / self.limit_amount) * Decimal(100)).quantize(
            Decimal("0.01")
        )

    model_config = ConfigDict(from_attributes=True)
