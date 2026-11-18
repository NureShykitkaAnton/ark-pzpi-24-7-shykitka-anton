"""Pydantic-схеми для створення, оновлення та читання тарифних планів."""

from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import UUID7


class TariffCreate(BaseModel):
    """Схема створення нового тарифного плану."""

    name: str = Field(min_length=2, max_length=120)
    currency: str = Field(default="UAH", pattern="^(UAH|USD|EUR)$")
    day_rate_per_kwh: Decimal = Field(
        default=Decimal("4.3200"), gt=Decimal(0), max_digits=10, decimal_places=4
    )
    night_multiplier: Decimal = Field(
        default=Decimal("0.5000"),
        gt=Decimal(0),
        le=Decimal(1),
        max_digits=5,
        decimal_places=4,
    )
    night_start_time: time = Field(default=time(23, 0, 0))
    night_end_time: time = Field(default=time(7, 0, 0))
    is_two_zone: bool = True
    is_default: bool = False


class TariffUpdate(BaseModel):
    """Схема часткового оновлення тарифного плану."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    currency: str | None = Field(default=None, pattern="^(UAH|USD|EUR)$")
    day_rate_per_kwh: Decimal | None = Field(
        default=None, gt=Decimal(0), max_digits=10, decimal_places=4
    )
    night_multiplier: Decimal | None = Field(
        default=None,
        gt=Decimal(0),
        le=Decimal(1),
        max_digits=5,
        decimal_places=4,
    )
    night_start_time: time | None = None
    night_end_time: time | None = None
    is_two_zone: bool | None = None
    is_default: bool | None = None


class TariffRead(BaseModel):
    """Схема представлення тарифного плану у відповідях REST API."""

    id: UUID7
    user_id: UUID7
    name: str
    currency: str
    day_rate_per_kwh: Decimal
    night_multiplier: Decimal
    night_start_time: time
    night_end_time: time
    is_two_zone: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
