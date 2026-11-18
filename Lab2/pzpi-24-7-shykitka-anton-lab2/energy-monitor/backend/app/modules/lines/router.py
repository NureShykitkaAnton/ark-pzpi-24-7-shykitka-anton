"""REST API маршрутизатор для управління лініями живлення та IoT-датчиками."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_user
from app.modules.lines.dependencies import get_power_line_service
from app.modules.lines.schemas import (
    PowerLineCreate,
    PowerLineRead,
    PowerLineUpdate,
    PowerLineWithTokenResponse,
)
from app.modules.lines.service import PowerLineService
from app.modules.users.models import User

router = APIRouter(prefix="/lines", tags=["lines"])


@router.post(
    "",
    response_model=PowerLineWithTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_power_line(
    data: PowerLineCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> PowerLineWithTokenResponse:
    """Створює нову лінію живлення та повертає згенерований токен для ESP32."""
    line, raw_token = await service.create_line(current_user.id, data)
    base_data = PowerLineRead.model_validate(line).model_dump()
    return PowerLineWithTokenResponse(**base_data, device_api_token=raw_token)


@router.get("", response_model=list[PowerLineRead])
async def list_power_lines(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[PowerLineRead]:
    """Повертає список усіх ліній живлення поточного користувача."""
    lines = await service.list_lines(current_user.id, skip=skip, limit=limit)
    return [PowerLineRead.model_validate(item) for item in lines]


@router.get("/{line_id}", response_model=PowerLineRead)
async def get_power_line(
    line_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> PowerLineRead:
    """Повертає детальну інформацію про обрану лінію живлення."""
    line = await service.get_user_line(line_id, current_user.id)
    return PowerLineRead.model_validate(line)


@router.patch("/{line_id}", response_model=PowerLineRead)
async def update_power_line(
    line_id: UUID7,
    data: PowerLineUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> PowerLineRead:
    """Оновлює параметри лінії живлення (тариф, поріг стрибка потужності, ліміт струму)."""
    line = await service.update_line(line_id, current_user.id, data)
    return PowerLineRead.model_validate(line)


@router.post(
    "/{line_id}/regenerate-token",
    response_model=PowerLineWithTokenResponse,
)
async def regenerate_device_token(
    line_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> PowerLineWithTokenResponse:
    """Перевипускає секретний API-ключ для IoT-клієнта ESP32."""
    line, raw_token = await service.regenerate_device_token(line_id, current_user.id)
    base_data = PowerLineRead.model_validate(line).model_dump()
    return PowerLineWithTokenResponse(**base_data, device_api_token=raw_token)


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_power_line(
    line_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> None:
    """Видаляє лінію живлення."""
    await service.delete_line(line_id, current_user.id)
