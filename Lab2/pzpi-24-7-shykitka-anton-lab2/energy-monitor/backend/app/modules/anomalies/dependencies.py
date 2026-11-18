"""Залежності FastAPI для модуля аномалій."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.anomalies.repository import AnomalyRepository
from app.modules.anomalies.service import AnomalyService
from app.modules.lines.dependencies import get_power_line_service
from app.modules.lines.service import PowerLineService


def get_anomaly_repository(session: SessionDep) -> AnomalyRepository:
    """Фабрика репозиторію аномалій."""
    return AnomalyRepository(session)


def get_anomaly_service(
    repo: Annotated[AnomalyRepository, Depends(get_anomaly_repository)],
    line_service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> AnomalyService:
    """Фабрика сервісу аномалій."""
    return AnomalyService(repo=repo, line_service=line_service)
