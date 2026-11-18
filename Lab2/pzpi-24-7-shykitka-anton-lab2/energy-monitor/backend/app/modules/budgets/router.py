"""REST API маршрутизатор для управління місячними бюджетами."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_user
from app.modules.budgets.dependencies import get_budget_service
from app.modules.budgets.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from app.modules.budgets.service import BudgetService
from app.modules.users.models import User

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetRead:
    """Створює новий місячний бюджетний ліміт для лінії живлення."""
    budget = await service.create_budget(current_user.id, data)
    return BudgetRead.model_validate(budget)


@router.get("", response_model=list[BudgetRead])
async def list_budgets(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    power_line_id: UUID7 | None = None,
    year: Annotated[int | None, Query(ge=2024, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> list[BudgetRead]:
    """Повертає список місячних бюджетів із фільтрацією за лінією, роком та місяцем."""
    budgets = await service.list_budgets(
        user_id=current_user.id,
        power_line_id=power_line_id,
        year=year,
        month=month,
    )
    return [BudgetRead.model_validate(b) for b in budgets]


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetRead:
    """Повертає детальний стан виконання бюджету та прогноз витрат на кінець місяця."""
    budget = await service.get_user_budget(budget_id, current_user.id)
    return BudgetRead.model_validate(budget)


@router.patch("/{budget_id}", response_model=BudgetRead)
async def update_budget(
    budget_id: UUID7,
    data: BudgetUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetRead:
    """Оновлює суму місячного ліміту або поріг попередження (80%)."""
    budget = await service.update_budget(budget_id, current_user.id, data)
    return BudgetRead.model_validate(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> None:
    """Видаляє місячний бюджетний ліміт."""
    await service.delete_budget(budget_id, current_user.id)
