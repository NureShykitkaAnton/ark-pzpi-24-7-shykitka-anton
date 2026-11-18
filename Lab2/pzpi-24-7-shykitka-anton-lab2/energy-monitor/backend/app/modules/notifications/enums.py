"""Перелічення платформ push-сповіщень та типів тригерів раннього попередження."""

from enum import StrEnum


class PushPlatform(StrEnum):
    """Мобільна або вебплатформа для доставки push-сповіщень (FCM / APNs)."""

    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB = "WEB"


class NotificationType(StrEnum):
    """Типи системних сповіщень про бюджет, перевантаження та стан датчика."""

    BUDGET_WARN_80 = "BUDGET_WARN_80"
    BUDGET_LIMIT_100 = "BUDGET_LIMIT_100"
    POWER_SPIKE = "POWER_SPIKE"
    OVERLOAD = "OVERLOAD"
    SENSOR_OFFLINE = "SENSOR_OFFLINE"
