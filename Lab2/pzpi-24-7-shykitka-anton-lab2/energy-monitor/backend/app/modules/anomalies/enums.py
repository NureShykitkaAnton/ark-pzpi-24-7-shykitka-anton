"""Перелічення типів аномальних подій у потоці енергетичної телеметрії."""

from enum import StrEnum


class AnomalyType(StrEnum):
    """Класифікація аномалій мережі та потоку вимірювань."""

    POWER_SPIKE = "POWER_SPIKE"
    OVERLOAD = "OVERLOAD"
    TIME_GAP = "TIME_GAP"
    VOLTAGE_OUT_OF_RANGE = "VOLTAGE_OUT_OF_RANGE"
    SENSOR_OFFLINE = "SENSOR_OFFLINE"
