"""Залежності FastAPI для модуля тарифів."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.tariffs.repository import TariffRepository
from app.modules.tariffs.service import TariffService


def get_tariff_repository(session: SessionDep) -> TariffRepository:
    """Фабрика репозиторію тарифів."""
    return TariffRepository(session)


def get_tariff_service(
    repo: Annotated[TariffRepository, Depends(get_tariff_repository)],
) -> TariffService:
    """Фабрика сервісу тарифів."""
    return TariffService(repo)
