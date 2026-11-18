"""ORM-модель тарифного плану на електроенергію з підтримкою двозонного обліку."""

import uuid
from datetime import time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.lines.models import PowerLine
    from app.modules.users.models import User


class Tariff(Base, UUIDMixin, TimestampMixin):
    """Таблиця тарифних планів (однозонні та двозонні «день/ніч»)."""

    __tablename__ = "tariffs"

    __table_args__ = (
        CheckConstraint("day_rate_per_kwh > 0", name="ck_tariffs_positive_day_rate"),
        CheckConstraint(
            "night_multiplier > 0 AND night_multiplier <= 1",
            name="ck_tariffs_valid_night_multiplier",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), server_default="UAH", default="UAH", nullable=False
    )
    day_rate_per_kwh: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("4.3200"), nullable=False
    )
    night_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.5000"), nullable=False
    )
    night_start_time: Mapped[time] = mapped_column(
        Time, default=time(23, 0, 0), nullable=False
    )
    night_end_time: Mapped[time] = mapped_column(
        Time, default=time(7, 0, 0), nullable=False
    )
    is_two_zone: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="tariffs")
    power_lines: Mapped[list[PowerLine]] = relationship(
        "PowerLine", back_populates="tariff"
    )
