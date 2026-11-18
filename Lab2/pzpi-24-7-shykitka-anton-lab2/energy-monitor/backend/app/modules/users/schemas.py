"""Схеми валідації та серіалізації даних користувача (Pydantic v2)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.types import UUID7
from app.modules.users.enums import (
    MeasurementSystem,
    SubscriptionTier,
    UserRole,
    UserStatus,
)


class UserBase(BaseModel):
    """Базові атрибути профілю користувача."""

    email: EmailStr
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)


class UserUpdate(BaseModel):
    """Схема оновлення профілю та параметрів локалізації користувача."""

    first_name: str | None = Field(default=None, min_length=2, max_length=50)
    last_name: str | None = Field(default=None, min_length=2, max_length=50)
    locale: str | None = Field(default=None, pattern="^(uk|en)$")
    timezone: str | None = Field(default=None, max_length=64)
    measurement_system: MeasurementSystem | None = None


class UserAdminUpdate(BaseModel):
    """Схема адміністративного оновлення статусу, ролі або рівня підписки."""

    status: UserStatus | None = None
    role: UserRole | None = None
    subscription_tier: SubscriptionTier | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None


class PasswordChangeRequest(BaseModel):
    """Схема запиту на зміну пароля користувача."""

    new_password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    """Схема повернення повної інформації про користувача клієнту."""

    id: UUID7
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.USER
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    locale: str = "uk"
    timezone: str = "Europe/Kyiv"
    measurement_system: MeasurementSystem = MeasurementSystem.METRIC
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
