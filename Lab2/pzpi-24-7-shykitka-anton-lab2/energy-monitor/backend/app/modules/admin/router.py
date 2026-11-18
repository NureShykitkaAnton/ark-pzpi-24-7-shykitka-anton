"""REST API маршрутизатор для журналу аудиту, резервного копіювання та експорту/імпорту."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.core.types import UUID7
from app.modules.admin.dependencies import get_admin_service
from app.modules.admin.schemas import (
    AuditLogRead,
    SystemBackupRead,
    SystemExportBundle,
    SystemImportRequest,
)
from app.modules.admin.service import AdminService
from app.modules.auth.dependencies import get_current_superuser, get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/audit-logs",
    response_model=list[AuditLogRead],
    dependencies=[Depends(get_current_superuser)],
)
async def list_audit_logs(
    service: Annotated[AdminService, Depends(get_admin_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[AuditLogRead]:
    """Повертає журнал аудиту дій у системі (доступно адміністратору)."""
    logs = await service.list_audit_logs(skip=skip, limit=limit)
    return [AuditLogRead.model_validate(item) for item in logs]


@router.post(
    "/backups",
    response_model=SystemBackupRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_system_backup(
    current_admin: Annotated[User, Depends(get_current_superuser)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> SystemBackupRead:
    """Ініціює створення резервної копії бази даних із обчисленням контрольної суми SHA-256."""
    backup = await service.create_backup(current_admin.id)
    return SystemBackupRead.model_validate(backup)


@router.get(
    "/backups",
    response_model=list[SystemBackupRead],
    dependencies=[Depends(get_current_superuser)],
)
async def list_system_backups(
    service: Annotated[AdminService, Depends(get_admin_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[SystemBackupRead]:
    """Повертає список створених резервних копій бази даних."""
    backups = await service.list_backups(skip=skip, limit=limit)
    return [SystemBackupRead.model_validate(b) for b in backups]


@router.post(
    "/backups/{backup_id}/verify",
    response_model=SystemBackupRead,
)
async def verify_backup_restore_integrity(
    backup_id: UUID7,
    current_admin: Annotated[User, Depends(get_current_superuser)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> SystemBackupRead:
    """Перевіряє цілісність файлу резервної копії та валідність його структури для відновлення."""
    backup = await service.verify_backup_integrity(backup_id, current_admin.id)
    return SystemBackupRead.model_validate(backup)


@router.get("/export", response_model=SystemExportBundle)
async def export_user_configuration(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> SystemExportBundle:
    """Експортує конфігурацію ліній, тарифів і бюджетів із контрольною сумою цілісності."""
    return await service.export_user_data(current_user.id)


@router.post("/import")
async def import_user_configuration(
    data: SystemImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> dict[str, Any]:
    """Імпортує налаштування користувача з перевіркою цілісності."""
    return await service.import_user_data(current_user.id, data)
