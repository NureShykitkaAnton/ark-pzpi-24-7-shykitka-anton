"""Схеми відповіді модуля перевірки стану системи."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Модель стану працездатності сервера та підключення до СУБД."""

    status: str
    database: str
    version: str
