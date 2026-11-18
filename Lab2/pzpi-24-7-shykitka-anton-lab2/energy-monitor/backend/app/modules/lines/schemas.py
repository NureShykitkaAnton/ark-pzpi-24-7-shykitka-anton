"""Pydantic-схеми для управління лініями живлення та реєстрації IoT-пристроїв."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import UUID7


class PowerLineCreate(BaseModel):
    """Схема створення нової лінії живлення та реєстрації датчика ESP32."""

    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    device_uid: str = Field(
        min_length=3,
        max_length=64,
        description="Унікальний апаратний ідентифікатор або MAC-адреса ESP32",
    )
    tariff_id: UUID7 | None = None
    nominal_voltage: Decimal = Field(default=Decimal("230.00"), gt=Decimal(0))
    max_current_limit: Decimal = Field(default=Decimal("25.00"), gt=Decimal(0))
    spike_threshold_watts: Decimal = Field(default=Decimal("800.00"), gt=Decimal(0))
    sampling_interval_sec: int = Field(default=5, ge=1, le=3600)


class PowerLineUpdate(BaseModel):
    """Схема оновлення параметрів лінії живлення."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    tariff_id: UUID7 | None = None
    nominal_voltage: Decimal | None = Field(default=None, gt=Decimal(0))
    max_current_limit: Decimal | None = Field(default=None, gt=Decimal(0))
    spike_threshold_watts: Decimal | None = Field(default=None, gt=Decimal(0))
    sampling_interval_sec: int | None = Field(default=None, ge=1, le=3600)
    is_active: bool | None = None


class PowerLineRead(BaseModel):
    """Схема відображення даних про лінію живлення."""

    id: UUID7
    user_id: UUID7
    tariff_id: UUID7 | None = None
    name: str
    description: str | None = None
    device_uid: str
    nominal_voltage: Decimal
    max_current_limit: Decimal
    spike_threshold_watts: Decimal
    sampling_interval_sec: int
    is_active: bool
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PowerLineWithTokenResponse(PowerLineRead):
    """Схема відповіді при створенні лінії або перевипуску ключа IoT-пристрою."""

    device_api_token: str = Field(
        description="Відкритий API-ключ для прошивки мікроконтролера ESP32 (показується одноразово)"
    )
