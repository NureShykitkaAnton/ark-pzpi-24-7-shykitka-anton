"""ORM-моделі часових рядів телеметрії (TelemetryReading) та профілів навантаження (LoadProfile)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.lines.models import PowerLine


class TelemetryReading(Base, UUIDMixin, TimestampMixin):
    """Таблиця часових рядів вимірювань напруги, струму, активної потужності та вартості."""

    __tablename__ = "telemetry_readings"

    __table_args__ = (
        Index(
            "ix_telemetry_line_recorded_at",
            "power_line_id",
            "recorded_at",
        ),
    )

    power_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_lines.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    voltage_rms: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    current_rms: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    active_power: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    power_factor: Mapped[Decimal] = mapped_column(
        Numeric(5, 3), default=Decimal("1.000"), nullable=False
    )

    energy_delta_kwh: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0.000000"), nullable=False
    )
    tariff_zone: Mapped[str] = mapped_column(
        String(16), default="DAY", server_default="DAY", nullable=False
    )
    cost_delta: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000"), nullable=False
    )

    is_buffered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_interpolated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    power_line: Mapped[PowerLine] = relationship(
        "PowerLine", back_populates="telemetry_readings"
    )


class LoadProfile(Base, UUIDMixin, TimestampMixin):
    """Таблиця збережених історичних або еталонних профілів навантаження для повторного програвання."""

    __tablename__ = "load_profiles"

    power_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_lines.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    readings_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    power_line: Mapped[PowerLine] = relationship(
        "PowerLine", back_populates="load_profiles"
    )
