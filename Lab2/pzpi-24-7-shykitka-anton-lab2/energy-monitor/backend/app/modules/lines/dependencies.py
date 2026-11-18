"""Залежності FastAPI для модуля ліній живлення та IoT-автентифікації."""

from typing import Annotated

from fastapi import Depends, Header

from app.core.database import SessionDep
from app.core.exceptions import UnauthorizedException
from app.core.security import hash_token
from app.modules.lines.models import PowerLine
from app.modules.lines.repository import PowerLineRepository
from app.modules.lines.service import PowerLineService


def get_power_line_repository(session: SessionDep) -> PowerLineRepository:
    """Фабрика репозиторію ліній живлення."""
    return PowerLineRepository(session)


def get_power_line_service(
    repo: Annotated[PowerLineRepository, Depends(get_power_line_repository)],
) -> PowerLineService:
    """Фабрика сервісу ліній живлення."""
    return PowerLineService(repo)


async def get_Optional_iot_line(
    repo: Annotated[PowerLineRepository, Depends(get_power_line_repository)],
    x_device_token: Annotated[str | None, Header(alias="X-Device-Token")] = None,
) -> PowerLine | None:
    """Перевіряє заголовок X-Device-Token від мікроконтролера ESP32, якщо він переданий."""
    if not x_device_token:
        return None
    token_hash = hash_token(x_device_token.strip())
    line = await repo.get_by_token_hash(token_hash)
    if not line or not line.is_active:
        raise UnauthorizedException("Invalid or inactive IoT device token")
    return line
