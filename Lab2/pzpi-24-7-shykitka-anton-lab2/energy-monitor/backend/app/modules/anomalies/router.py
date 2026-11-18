"""REST API маршрутизатор для перегляду аномалій, маркування приладів та запитів до LLM."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.types import UUID7
from app.modules.anomalies.dependencies import get_anomaly_service
from app.modules.anomalies.enums import AnomalyType
from app.modules.anomalies.schemas import (
    AnomalyEventRead,
    AnomalyExplainRequest,
    AnomalyLabelUpdate,
)
from app.modules.anomalies.service import AnomalyService
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyEventRead])
async def list_anomalies(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
    power_line_id: UUID7 | None = None,
    anomaly_type: AnomalyType | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[AnomalyEventRead]:
    """Повертає список зафіксованих стрибків потужності та аномалій мережі."""
    events = await service.list_anomalies(
        user_id=current_user.id,
        power_line_id=power_line_id,
        anomaly_type=anomaly_type,
        skip=skip,
        limit=limit,
    )
    return [AnomalyEventRead.model_validate(ev) for ev in events]


@router.get("/{anomaly_id}", response_model=AnomalyEventRead)
async def get_anomaly(
    anomaly_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
) -> AnomalyEventRead:
    """Повертає деталі конкретної аномальної події."""
    event = await service.get_user_anomaly(anomaly_id, current_user.id)
    return AnomalyEventRead.model_validate(event)


@router.patch("/{anomaly_id}/label", response_model=AnomalyEventRead)
async def label_anomaly_appliance(
    anomaly_id: UUID7,
    data: AnomalyLabelUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
) -> AnomalyEventRead:
    """Дозволяє користувачу позначити увімкнений прилад для зафіксованого стрибка потужності."""
    event = await service.label_appliance(anomaly_id, current_user.id, data)
    return AnomalyEventRead.model_validate(event)


@router.post("/{anomaly_id}/explain", response_model=AnomalyEventRead)
async def explain_anomaly_with_llm(
    anomaly_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
    data: AnomalyExplainRequest | None = None,
) -> AnomalyEventRead:
    """Генерує текстове пояснення стрибка потужності природною мовою за допомогою LLM."""
    locale = data.locale if data else current_user.locale
    event = await service.generate_llm_explanation(
        anomaly_id, current_user.id, locale=locale
    )
    return AnomalyEventRead.model_validate(event)
