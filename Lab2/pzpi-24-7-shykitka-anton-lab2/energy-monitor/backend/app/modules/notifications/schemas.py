"""Pydantic-схеми для реєстрації push-токенів пристроїв та роботи зі сповіщеннями."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import UUID7
from app.modules.notifications.enums import NotificationType, PushPlatform


class PushTokenCreate(BaseModel):
    """Схема реєстрації токена мобільного пристрою (FCM / APNs)."""

    platform: PushPlatform
    device_token: str = Field(min_length=10, max_length=512)
    device_name: str | None = Field(default=None, max_length=120)


class PushTokenRead(BaseModel):
    """Схема представлення зареєстрованого push-токена."""

    id: UUID7
    user_id: UUID7
    platform: PushPlatform
    device_token: str
    device_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    """Схема представлення сповіщення у відповідях REST API."""

    id: UUID7
    user_id: UUID7
    power_line_id: UUID7 | None = None
    notification_type: NotificationType
    title: str
    body: str
    is_read: bool
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
