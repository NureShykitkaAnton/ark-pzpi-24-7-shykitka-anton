"""Залежності FastAPI для модуля системного адміністрування."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.admin.repository import AuditLogRepository, SystemBackupRepository
from app.modules.admin.service import AdminService
from app.modules.budgets.dependencies import get_budget_repository
from app.modules.budgets.repository import BudgetRepository
from app.modules.lines.dependencies import get_power_line_repository
from app.modules.lines.repository import PowerLineRepository
from app.modules.tariffs.dependencies import get_tariff_repository
from app.modules.tariffs.repository import TariffRepository


def get_audit_log_repository(session: SessionDep) -> AuditLogRepository:
    """Фабрика репозиторію журналу аудиту."""
    return AuditLogRepository(session)


def get_system_backup_repository(session: SessionDep) -> SystemBackupRepository:
    """Фабрика репозиторію резервних копій."""
    return SystemBackupRepository(session)


def get_admin_service(
    audit_repo: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    backup_repo: Annotated[
        SystemBackupRepository, Depends(get_system_backup_repository)
    ],
    tariff_repo: Annotated[TariffRepository, Depends(get_tariff_repository)],
    line_repo: Annotated[PowerLineRepository, Depends(get_power_line_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
) -> AdminService:
    """Фабрика сервісу адміністрування."""
    return AdminService(
        audit_repo=audit_repo,
        backup_repo=backup_repo,
        tariff_repo=tariff_repo,
        line_repo=line_repo,
        budget_repo=budget_repo,
    )
