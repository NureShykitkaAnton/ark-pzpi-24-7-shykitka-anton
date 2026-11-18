"""ORM-модель користувача програмної системи контролю енергоспоживання."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, false
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin
from app.modules.users.enums import (
    MeasurementSystem,
    SubscriptionTier,
    UserRole,
    UserStatus,
)

if TYPE_CHECKING:
    from app.modules.auth.models import RefreshToken
    from app.modules.lines.models import PowerLine
    from app.modules.notifications.models import Notification, PushToken
    from app.modules.tariffs.models import Tariff


class User(Base, UUIDMixin, TimestampMixin):
    """Таблиця облікових записів споживачів та адміністраторів системи."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=20,
        ),
        server_default=UserStatus.ACTIVE.value,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=20,
        ),
        server_default=UserRole.USER.value,
        nullable=False,
    )
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(
            SubscriptionTier,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=20,
        ),
        server_default=SubscriptionTier.FREE.value,
        nullable=False,
    )

    # Параметри інтернаціоналізації та локалізації
    locale: Mapped[str] = mapped_column(
        String(10), server_default="uk", default="uk", nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(64), server_default="Europe/Kyiv", default="Europe/Kyiv", nullable=False
    )
    measurement_system: Mapped[MeasurementSystem] = mapped_column(
        SAEnum(
            MeasurementSystem,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=20,
        ),
        server_default=MeasurementSystem.METRIC.value,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=false(), nullable=False
    )

    # Відношення з іншими таблицями БД
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    power_lines: Mapped[list[PowerLine]] = relationship(
        "PowerLine",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tariffs: Mapped[list[Tariff]] = relationship(
        "Tariff",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    push_tokens: Mapped[list[PushToken]] = relationship(
        "PushToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
