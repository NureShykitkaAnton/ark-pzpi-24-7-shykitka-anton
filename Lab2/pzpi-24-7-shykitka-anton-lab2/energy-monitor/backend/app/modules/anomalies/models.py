"""ORM-модель зафіксованих аномалій навантаження, маркування приладів та висновків LLM."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin
from app.modules.anomalies.enums import AnomalyType

if TYPE_CHECKING:
    from app.modules.lines.models import PowerLine


class AnomalyEvent(Base, UUIDMixin, TimestampMixin):
    """Таблиця аномальних стрибків потужності (ΔP > P_threshold), перевантажень та часових пропусків."""

    __tablename__ = "anomaly_events"

    __table_args__ = (
        Index(
            "ix_anomaly_events_line_detected_at",
            "power_line_id",
            "detected_at",
        ),
    )

    power_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_lines.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    anomaly_type: Mapped[AnomalyType] = mapped_column(
        SAEnum(
            AnomalyType,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=40,
        ),
        nullable=False,
    )
    delta_power_watts: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    peak_power_watts: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    user_appliance_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    power_line: Mapped[PowerLine] = relationship(
        "PowerLine", back_populates="anomaly_events"
    )
