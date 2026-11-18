"""Залежності FastAPI для модуля фінансових бюджетів."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.budgets.repository import BudgetRepository
from app.modules.budgets.service import BudgetService
from app.modules.lines.dependencies import get_power_line_service
from app.modules.lines.service import PowerLineService


def get_budget_repository(session: SessionDep) -> BudgetRepository:
    """Фабрика репозиторію бюджетів."""
    return BudgetRepository(session)


def get_budget_service(
    repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    line_service: Annotated[PowerLineService, Depends(get_power_line_service)],
) -> BudgetService:
    """Фабрика сервісу бюджетів."""
    return BudgetService(repo=repo, line_service=line_service)
