"""Залежності FastAPI для модуля телеметрії."""

from typing import Annotated

from fastapi import Depends, Header

from app.core.database import SessionDep
from app.modules.anomalies.dependencies import get_anomaly_repository
from app.modules.anomalies.repository import AnomalyRepository
from app.modules.budgets.dependencies import get_budget_service
from app.modules.budgets.service import BudgetService
from app.modules.lines.dependencies import (
    get_power_line_repository,
    get_power_line_service,
)
from app.modules.lines.repository import PowerLineRepository
from app.modules.lines.service import PowerLineService
from app.modules.tariffs.dependencies import get_tariff_repository
from app.modules.tariffs.repository import TariffRepository
from app.modules.telemetry.repository import (
    LoadProfileRepository,
    TelemetryRepository,
)
from app.modules.telemetry.service import TelemetryService
from app.modules.users.dependencies import get_user_service
from app.modules.users.models import User
from app.modules.users.service import UserService


def get_telemetry_repository(session: SessionDep) -> TelemetryRepository:
    """Фабрика репозиторію телеметрії."""
    return TelemetryRepository(session)


def get_load_profile_repository(session: SessionDep) -> LoadProfileRepository:
    """Фабрика репозиторію профілів навантаження."""
    return LoadProfileRepository(session)


def get_telemetry_service(
    telemetry_repo: Annotated[TelemetryRepository, Depends(get_telemetry_repository)],
    profile_repo: Annotated[
        LoadProfileRepository, Depends(get_load_profile_repository)
    ],
    line_repo: Annotated[PowerLineRepository, Depends(get_power_line_repository)],
    line_service: Annotated[PowerLineService, Depends(get_power_line_service)],
    tariff_repo: Annotated[TariffRepository, Depends(get_tariff_repository)],
    anomaly_repo: Annotated[AnomalyRepository, Depends(get_anomaly_repository)],
    budget_service: Annotated[BudgetService, Depends(get_budget_service)],
) -> TelemetryService:
    """Фабрика сервісу телеметрії."""
    return TelemetryService(
        telemetry_repo=telemetry_repo,
        profile_repo=profile_repo,
        line_repo=line_repo,
        line_service=line_service,
        tariff_repo=tariff_repo,
        anomaly_repo=anomaly_repo,
        budget_service=budget_service,
    )


async def get_optional_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_header: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User | None:
    """Повертає авторизованого користувача, якщо передано заголовок Authorization Bearer."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    import uuid

    from app.core.security import decode_token

    token = auth_header.removeprefix("Bearer ").strip()
    payload = decode_token(token, expected_type="access")
    sub = payload.get("sub")
    if not sub:
        return None
    return await user_service.get_by_id(uuid.UUID(sub))
