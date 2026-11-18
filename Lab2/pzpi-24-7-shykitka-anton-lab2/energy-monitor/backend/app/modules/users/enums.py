"""Перелічення статусів, ролей, тарифних підписок та параметрів локалізації користувачів."""

from enum import StrEnum


class UserStatus(StrEnum):
    """Статус облікового запису користувача."""

    ACTIVE = "Active"
    BANNED = "Banned"


class UserRole(StrEnum):
    """Роль користувача в системі."""

    USER = "User"
    ADMIN = "Admin"


class SubscriptionTier(StrEnum):
    """Рівень підписки за моделлю монетизації Freemium."""

    FREE = "Free"
    PRO = "Pro"


class MeasurementSystem(StrEnum):
    """Система одиниць вимірювання (інтернаціоналізація)."""

    METRIC = "Metric"
    IMPERIAL = "Imperial"
