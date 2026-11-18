"""ORM-моделі реєстру push-токенів (PushToken) та журналу сповіщень (Notification)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDMixin
from app.modules.notifications.enums import NotificationType, PushPlatform

if TYPE_CHECKING:
    from app.modules.lines.models import PowerLine
    from app.modules.users.models import User


class PushToken(Base, UUIDMixin, TimestampMixin):
    """Таблиця токенів мобільних пристроїв для push-сервісів Firebase Cloud Messaging та APNs."""

    __tablename__ = "push_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    platform: Mapped[PushPlatform] = mapped_column(
        SAEnum(
            PushPlatform,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=20,
        ),
        nullable=False,
    )
    device_token: Mapped[str] = mapped_column(
        String(512), unique=True, index=True, nullable=False
    )
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="push_tokens")


class Notification(Base, UUIDMixin, TimestampMixin):
    """Таблиця системних і push-сповіщень про бюджет (80%/100%), стрибки та втрату зв'язку з ESP32."""

    __tablename__ = "notifications"

    __table_args__ = (
        Index(
            "ix_notifications_user_created_at",
            "user_id",
            "created_at",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    power_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("power_lines.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(
            NotificationType,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            length=40,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="notifications")
    power_line: Mapped[PowerLine | None] = relationship(
        "PowerLine", back_populates="notifications"
    )
