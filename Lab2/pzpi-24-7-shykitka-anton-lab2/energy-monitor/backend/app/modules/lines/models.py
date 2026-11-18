"""ORM-модель лінії живлення та прив'язаного сенсорного модуля ESP32."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.anomalies.models import AnomalyEvent
    from app.modules.budgets.models import Budget
    from app.modules.notifications.models import Notification
    from app.modules.tariffs.models import Tariff
    from app.modules.telemetry.models import LoadProfile, TelemetryReading
    from app.modules.users.models import User


class PowerLine(Base, UUIDMixin, TimestampMixin):
    """Таблиця ліній електроживлення та налаштувань вимірювальних пристроїв ESP32."""

    __tablename__ = "power_lines"

    __table_args__ = (
        CheckConstraint("nominal_voltage > 0", name="ck_power_lines_positive_voltage"),
        CheckConstraint(
            "max_current_limit > 0", name="ck_power_lines_positive_current"
        ),
        CheckConstraint(
            "spike_threshold_watts > 0", name="ck_power_lines_positive_spike"
        ),
        CheckConstraint(
            "sampling_interval_sec >= 1", name="ck_power_lines_valid_interval"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tariff_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tariffs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    device_uid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    device_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    nominal_voltage: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("230.00"), nullable=False
    )
    max_current_limit: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("25.00"), nullable=False
    )
    spike_threshold_watts: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("800.00"), nullable=False
    )
    sampling_interval_sec: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="power_lines")
    tariff: Mapped[Tariff | None] = relationship("Tariff", back_populates="power_lines")
    budgets: Mapped[list[Budget]] = relationship(
        "Budget", back_populates="power_line", cascade="all, delete-orphan"
    )
    telemetry_readings: Mapped[list[TelemetryReading]] = relationship(
        "TelemetryReading",
        back_populates="power_line",
        cascade="all, delete-orphan",
    )
    anomaly_events: Mapped[list[AnomalyEvent]] = relationship(
        "AnomalyEvent",
        back_populates="power_line",
        cascade="all, delete-orphan",
    )
    load_profiles: Mapped[list[LoadProfile]] = relationship(
        "LoadProfile",
        back_populates="power_line",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="power_line",
    )
