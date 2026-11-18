"""Pydantic-схеми для журналу аудиту, резервного копіювання та експорту/імпорту."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.types import UUID7


class AuditLogRead(BaseModel):
    """Схема запису журналу аудиту."""

    id: UUID7
    user_id: UUID7 | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    ip_address: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemBackupRead(BaseModel):
    """Схема інформації про резервну копію бази даних."""

    id: UUID7
    created_by_id: UUID7 | None = None
    filename: str
    file_size_bytes: int
    checksum_sha256: str
    status: str
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemExportBundle(BaseModel):
    """Схема повного експорту конфігурацій користувача з контрольною сумою цілісності."""

    exported_at: datetime
    user_id: UUID7
    tariffs: list[dict[str, Any]]
    power_lines: list[dict[str, Any]]
    budgets: list[dict[str, Any]]
    checksum_sha256: str


class SystemImportRequest(BaseModel):
    """Схема імпорту налаштувань із обов'язковою перевіркою цілісності."""

    tariffs: list[dict[str, Any]] = []
    budgets: list[dict[str, Any]] = []
    checksum_sha256: str | None = None
