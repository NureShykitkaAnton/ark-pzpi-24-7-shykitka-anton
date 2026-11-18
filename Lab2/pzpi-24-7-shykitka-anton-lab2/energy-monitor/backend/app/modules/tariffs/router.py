"""REST API маршрутизатор для управління тарифними планами."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_user
from app.modules.tariffs.dependencies import get_tariff_service
from app.modules.tariffs.schemas import TariffCreate, TariffRead, TariffUpdate
from app.modules.tariffs.service import TariffService
from app.modules.users.models import User

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.post("", response_model=TariffRead, status_code=status.HTTP_201_CREATED)
async def create_tariff(
    data: TariffCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TariffService, Depends(get_tariff_service)],
) -> TariffRead:
    """Створює новий однозонний або двозонний тарифний план."""
    tariff = await service.create_tariff(current_user.id, data)
    return TariffRead.model_validate(tariff)


@router.get("", response_model=list[TariffRead])
async def list_tariffs(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TariffService, Depends(get_tariff_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TariffRead]:
    """Повертає список тарифних планів поточного користувача."""
    tariffs = await service.list_tariffs(current_user.id, skip=skip, limit=limit)
    return [TariffRead.model_validate(t) for t in tariffs]


@router.get("/{tariff_id}", response_model=TariffRead)
async def get_tariff(
    tariff_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TariffService, Depends(get_tariff_service)],
) -> TariffRead:
    """Повертає детальну інформацію про обраний тариф."""
    tariff = await service.get_user_tariff(tariff_id, current_user.id)
    return TariffRead.model_validate(tariff)


@router.patch("/{tariff_id}", response_model=TariffRead)
async def update_tariff(
    tariff_id: UUID7,
    data: TariffUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TariffService, Depends(get_tariff_service)],
) -> TariffRead:
    """Оновлює параметри тарифу (ставку, нічний коефіцієнт, часові межі)."""
    tariff = await service.update_tariff(tariff_id, current_user.id, data)
    return TariffRead.model_validate(tariff)


@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tariff(
    tariff_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TariffService, Depends(get_tariff_service)],
) -> None:
    """Видаляє тарифний план."""
    await service.delete_tariff(tariff_id, current_user.id)
