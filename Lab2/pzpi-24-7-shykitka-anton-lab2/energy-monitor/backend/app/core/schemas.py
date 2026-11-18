"""Спільні схеми відповідей Pydantic."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Універсальна схема текстового повідомлення від сервера."""

    message: str
    detail: str | None = None
