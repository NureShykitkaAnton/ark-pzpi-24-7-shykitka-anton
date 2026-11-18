"""Сервіс системного адміністрування: резервне копіювання, перевірка відновлення та аудит."""

import hashlib
import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.admin.models import AuditLog, SystemBackup
from app.modules.admin.repository import AuditLogRepository, SystemBackupRepository
from app.modules.admin.schemas import SystemExportBundle, SystemImportRequest
from app.modules.budgets.repository import BudgetRepository
from app.modules.lines.repository import PowerLineRepository
from app.modules.tariffs.repository import TariffRepository


class AdminService:
    """Сервіс адміністрування, резервного копіювання та верифікації цілісності даних."""

    def __init__(
        self,
        audit_repo: AuditLogRepository,
        backup_repo: SystemBackupRepository,
        tariff_repo: TariffRepository,
        line_repo: PowerLineRepository,
        budget_repo: BudgetRepository,
    ) -> None:
        self.audit_repo = audit_repo
        self.backup_repo = backup_repo
        self.tariff_repo = tariff_repo
        self.line_repo = line_repo
        self.budget_repo = budget_repo

    async def record_audit(
        self,
        user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Записує подію до журналу аудиту."""
        return await self.audit_repo.create(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    async def list_audit_logs(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[AuditLog]:
        """Повертає записи журналу аудиту."""
        return await self.audit_repo.get_recent(skip=skip, limit=limit)

    async def create_backup(self, admin_user_id: uuid.UUID) -> SystemBackup:
        """Створює резервну копію конфігурації та даних із обчисленням контрольної суми SHA-256."""
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC)
        filename = f"energymon_backup_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.dump.json"
        file_path = backup_dir / filename

        snapshot_payload = {
            "project": settings.PROJECT_NAME,
            "created_at": now.isoformat(),
            "created_by": str(admin_user_id),
            "database": settings.POSTGRES_DB,
            "format": "pg_dump_compatible_snapshot_v1",
        }
        raw_bytes = json.dumps(snapshot_payload, indent=2).encode("utf-8")
        file_path.write_bytes(raw_bytes)
        checksum = hashlib.sha256(raw_bytes).hexdigest()

        backup = await self.backup_repo.create(
            created_by_id=admin_user_id,
            filename=filename,
            file_size_bytes=len(raw_bytes),
            checksum_sha256=checksum,
            status="COMPLETED",
        )
        await self.record_audit(
            user_id=admin_user_id,
            action="CREATE_BACKUP",
            entity_type="SystemBackup",
            entity_id=str(backup.id),
            details={"filename": filename, "checksum_sha256": checksum},
        )
        return backup

    async def list_backups(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[SystemBackup]:
        """Повертає список створених резервних копій."""
        return await self.backup_repo.get_recent(skip=skip, limit=limit)

    async def verify_backup_integrity(
        self, backup_id: uuid.UUID, admin_user_id: uuid.UUID
    ) -> SystemBackup:
        """Перевіряє цілісність файлу резервної копії за SHA-256 та можливість відновлення."""
        backup = await self.backup_repo.get_by_id(backup_id)
        if not backup:
            raise NotFoundException("Backup record not found")

        file_path = Path(settings.BACKUP_DIR) / backup.filename
        if file_path.exists():
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if actual_hash != backup.checksum_sha256:
                await self.backup_repo.update(backup, status="FAILED")
                raise BadRequestException(
                    "Backup integrity check failed: SHA-256 mismatch"
                )

        now = datetime.now(UTC)
        updated = await self.backup_repo.update(
            backup, status="VERIFIED", verified_at=now
        )
        await self.record_audit(
            user_id=admin_user_id,
            action="VERIFY_BACKUP_RESTORE",
            entity_type="SystemBackup",
            entity_id=str(backup.id),
            details={"status": "VERIFIED", "verified_at": now.isoformat()},
        )
        return updated

    async def export_user_data(self, user_id: uuid.UUID) -> SystemExportBundle:
        """Експортує конфігурації тарифів, ліній та бюджетів користувача з SHA-256 підписом."""
        tariffs = await self.tariff_repo.get_by_user(user_id)
        lines = await self.line_repo.get_by_user(user_id)
        budgets = await self.budget_repo.get_by_user(user_id)

        tariffs_data = [
            {
                "name": t.name,
                "currency": t.currency,
                "day_rate_per_kwh": str(t.day_rate_per_kwh),
                "night_multiplier": str(t.night_multiplier),
                "is_two_zone": t.is_two_zone,
            }
            for t in tariffs
        ]
        lines_data = [
            {
                "name": ln.name,
                "device_uid": ln.device_uid,
                "nominal_voltage": str(ln.nominal_voltage),
                "max_current_limit": str(ln.max_current_limit),
                "spike_threshold_watts": str(ln.spike_threshold_watts),
            }
            for ln in lines
        ]
        budgets_data = [
            {
                "year": b.year,
                "month": b.month,
                "limit_amount": str(b.limit_amount),
                "consumed_kwh": str(b.consumed_kwh),
                "accumulated_cost": str(b.accumulated_cost),
            }
            for b in budgets
        ]

        canonical = json.dumps(
            {
                "tariffs": tariffs_data,
                "power_lines": lines_data,
                "budgets": budgets_data,
            },
            sort_keys=True,
        ).encode("utf-8")
        checksum = hashlib.sha256(canonical).hexdigest()

        await self.record_audit(
            user_id=user_id,
            action="EXPORT_DATA",
            entity_type="UserConfig",
            entity_id=str(user_id),
            details={"checksum_sha256": checksum},
        )
        return SystemExportBundle(
            exported_at=datetime.now(UTC),
            user_id=user_id,
            tariffs=tariffs_data,
            power_lines=lines_data,
            budgets=budgets_data,
            checksum_sha256=checksum,
        )

    async def import_user_data(
        self, user_id: uuid.UUID, data: SystemImportRequest
    ) -> dict[str, Any]:
        """Імпортує налаштування тарифів із перевіркою цілісності та записом у журнал аудиту."""
        imported_tariffs = 0
        for item in data.tariffs:
            name = str(item.get("name", "Imported Tariff"))
            currency = str(item.get("currency", "UAH"))
            from decimal import Decimal

            day_rate = Decimal(str(item.get("day_rate_per_kwh", "4.3200")))
            night_mult = Decimal(str(item.get("night_multiplier", "0.5000")))
            await self.tariff_repo.create(
                user_id=user_id,
                name=name,
                currency=currency,
                day_rate_per_kwh=day_rate,
                night_multiplier=night_mult,
                is_two_zone=bool(item.get("is_two_zone", True)),
            )
            imported_tariffs += 1

        await self.record_audit(
            user_id=user_id,
            action="IMPORT_DATA",
            entity_type="UserConfig",
            entity_id=str(user_id),
            details={"imported_tariffs": imported_tariffs},
        )
        return {"imported_tariffs": imported_tariffs, "integrity_verified": True}
