"""Pydantic-схеми для роботи з аномаліями, маркуванням приладів та LLM-поясненнями."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import UUID7
from app.modules.anomalies.enums import AnomalyType


class AnomalyLabelUpdate(BaseModel):
    """Схема швидкого позначення увімкненого побутового приладу користувачем."""

    user_appliance_label: str = Field(
        min_length=1,
        max_length=120,
        description="Назва побутового приладу (напр. Бойлер, Електрочайник, Пральна машина)",
    )
    is_acknowledged: bool = True


class AnomalyExplainRequest(BaseModel):
    """Параметри запиту на генерацію текстового пояснення від LLM."""

    locale: str = Field(default="uk", pattern="^(uk|en)$")


class AnomalyEventRead(BaseModel):
    """Схема представлення зафіксованої аномальної події у відповідях API."""

    id: UUID7
    power_line_id: UUID7
    detected_at: datetime
    anomaly_type: AnomalyType
    delta_power_watts: Decimal
    peak_power_watts: Decimal
    user_appliance_label: str | None = None
    llm_explanation: str | None = None
    is_acknowledged: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
