"""ORM-модель місячного бюджету споживання електроенергії на лінію живлення."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.lines.models import PowerLine


class Budget(Base, UUIDMixin, TimestampMixin):
    """Таблиця місячних фінансових бюджетів та лімітів споживання."""

    __tablename__ = "budgets"

    __table_args__ = (
        UniqueConstraint(
            "power_line_id", "year", "month", name="uq_budgets_line_year_month"
        ),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_budgets_valid_month"),
        CheckConstraint("limit_amount > 0", name="ck_budgets_positive_limit"),
        CheckConstraint(
            "warn_threshold_pct > 0 AND warn_threshold_pct <= 100",
            name="ck_budgets_valid_warn_pct",
        ),
    )

    power_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_lines.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    consumed_kwh: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000"), nullable=False
    )
    accumulated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    forecasted_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    warn_threshold_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("80.00"), nullable=False
    )
    warn_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    limit_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    power_line: Mapped[PowerLine] = relationship("PowerLine", back_populates="budgets")
