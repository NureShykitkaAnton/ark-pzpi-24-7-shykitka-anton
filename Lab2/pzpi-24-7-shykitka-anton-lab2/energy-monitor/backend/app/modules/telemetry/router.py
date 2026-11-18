"""REST API маршрутизатор для прийому телеметрії, вибірки часових рядів та програвання профілів."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.types import UUID7
from app.modules.auth.dependencies import get_current_user
from app.modules.lines.dependencies import get_Optional_iot_line
from app.modules.lines.models import PowerLine
from app.modules.telemetry.dependencies import (
    get_optional_user,
    get_telemetry_service,
)
from app.modules.telemetry.schemas import (
    LoadProfileCreate,
    LoadProfileRead,
    LoadProfileReplayRequest,
    LoadProfileReplayResult,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
    TelemetryReadingRead,
    TelemetrySummaryResponse,
)
from app.modules.telemetry.service import TelemetryService
from app.modules.users.models import User

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry(
    data: TelemetryIngestRequest,
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    iot_line: Annotated[PowerLine | None, Depends(get_Optional_iot_line)] = None,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> TelemetryIngestResponse:
    """Приймає телеметрію від сенсора ESP32 (за X-Device-Token) або авторизованого користувача."""
    user_id = current_user.id if current_user else None
    return await service.ingest_samples(data=data, iot_line=iot_line, user_id=user_id)


@router.get("", response_model=list[TelemetryReadingRead])
async def list_telemetry_readings(
    power_line_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[TelemetryReadingRead]:
    """Повертає часовий ряд відліків напруги, струму та потужності за вказаний інтервал."""
    readings = await service.list_readings(
        user_id=current_user.id,
        power_line_id=power_line_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return [TelemetryReadingRead.model_validate(r) for r in readings]


@router.get("/summary", response_model=TelemetrySummaryResponse)
async def get_telemetry_summary(
    power_line_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> TelemetrySummaryResponse:
    """Повертає агреговані показники споживання (день/ніч, вартість, середня та пікова потужність)."""
    return await service.get_summary(
        user_id=current_user.id,
        power_line_id=power_line_id,
        start_time=start_time,
        end_time=end_time,
    )


@router.post(
    "/profiles",
    response_model=LoadProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_load_profile(
    data: LoadProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
) -> LoadProfileRead:
    """Зберігає еталонний або історичний профіль навантаження у базі даних."""
    profile = await service.create_profile(current_user.id, data)
    return LoadProfileRead.model_validate(profile)


@router.get("/profiles", response_model=list[LoadProfileRead])
async def list_load_profiles(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    power_line_id: UUID7 | None = None,
) -> list[LoadProfileRead]:
    """Повертає список збережених профілів навантаження."""
    profiles = await service.list_profiles(
        user_id=current_user.id, power_line_id=power_line_id
    )
    return [LoadProfileRead.model_validate(p) for p in profiles]


@router.post(
    "/profiles/{profile_id}/replay",
    response_model=LoadProfileReplayResult,
)
async def replay_load_profile(
    profile_id: UUID7,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    data: LoadProfileReplayRequest | None = None,
) -> LoadProfileReplayResult:
    """Відтворює збережений профіль навантаження для моделювання витрат за обраним тарифом."""
    tariff_id = data.tariff_id if data else None
    return await service.replay_profile(
        profile_id=profile_id, user_id=current_user.id, tariff_id=tariff_id
    )
