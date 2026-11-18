"""Декларативна база моделей SQLAlchemy 2 та спільні міксини ідентифікаторів і часових міток."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовий клас для всіх ORM-моделей бази даних."""


class TimestampMixin:
    """Міксин для автоматичного ведення часових міток створення та оновлення запису в UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class UUIDMixin:
    """Міксин первинного ключа на основі впорядкованого за часом стандарту UUIDv7."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
        index=True,
    )
