"""Pydantic-схеми для прийому пакетів від ESP32, вибірки графіків та програвання профілів."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import UUID7


class TelemetrySampleInput(BaseModel):
    """Одиничний вимір від мікроконтролера ESP32 або з його кільцевого RAM-буфера."""

    recorded_at: datetime
    voltage_rms: Decimal = Field(ge=Decimal(0), le=Decimal(1000))
    current_rms: Decimal = Field(ge=Decimal(0), le=Decimal(500))
    active_power: Decimal | None = Field(
        default=None,
        ge=Decimal(0),
        description="Активна потужність P (Вт); якщо не передана — обчислюється як U_rms * I_rms * cos(phi)",
    )
    power_factor: Decimal = Field(
        default=Decimal("0.980"), ge=Decimal(0), le=Decimal(1)
    )
    is_buffered: bool = Field(
        default=False,
        description="Ознака того, що пакет був збережений у RAM-буфері ESP32 під час обриву зв'язку",
    )


class TelemetryIngestRequest(BaseModel):
    """Пакетний запит на завантаження телеметрії від IoT-клієнта або симулятора."""

    power_line_id: UUID7 | None = Field(
        default=None,
        description="Ідентифікатор лінії (необов'язковий при автентифікації через X-Device-Token)",
    )
    samples: list[TelemetrySampleInput] = Field(min_length=1, max_length=500)


class TelemetryReadingRead(BaseModel):
    """Схема одного збереженого відліку телеметрії."""

    id: UUID7
    power_line_id: UUID7
    recorded_at: datetime
    voltage_rms: Decimal
    current_rms: Decimal
    active_power: Decimal
    power_factor: Decimal
    energy_delta_kwh: Decimal
    tariff_zone: str
    cost_delta: Decimal
    is_buffered: bool
    is_interpolated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryIngestResponse(BaseModel):
    """Підсумок обробки пакета телеметрії сервером."""

    ingested_count: int
    interpolated_gaps_count: int
    anomalies_detected_count: int
    readings: list[TelemetryReadingRead]


class TelemetrySummaryResponse(BaseModel):
    """Агрегована статистика споживання та якості даних за обраний період."""

    power_line_id: UUID7
    total_readings: int
    interpolated_readings: int
    buffered_readings: int
    total_energy_kwh: Decimal
    day_energy_kwh: Decimal
    night_energy_kwh: Decimal
    total_cost: Decimal
    avg_power_watts: Decimal
    peak_power_watts: Decimal


class LoadProfileCreate(BaseModel):
    """Схема збереження профілю навантаження для ретроспективного аналізу."""

    power_line_id: UUID7
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    readings_payload: list[dict[str, Any]] = Field(min_length=1)


class LoadProfileRead(BaseModel):
    """Схема читання збереженого профілю навантаження."""

    id: UUID7
    power_line_id: UUID7
    name: str
    description: str | None = None
    readings_payload: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoadProfileReplayRequest(BaseModel):
    """Параметри повторного програвання профілю за альтернативним тарифом."""

    tariff_id: UUID7 | None = None


class LoadProfileReplayResult(BaseModel):
    """Результат моделювання витрат під час повторного програвання профілю."""

    profile_id: UUID7
    profile_name: str
    simulated_samples: int
    total_energy_kwh: Decimal
    day_energy_kwh: Decimal
    night_energy_kwh: Decimal
    simulated_total_cost: Decimal
    currency: str
