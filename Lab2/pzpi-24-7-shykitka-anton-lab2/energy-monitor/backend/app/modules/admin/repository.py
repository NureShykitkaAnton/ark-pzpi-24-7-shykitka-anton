"""Репозиторії для журналу аудиту та реєстру резервних копій."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import BaseRepository
from app.modules.admin.models import AuditLog, SystemBackup


class AuditLogRepository(BaseRepository[AuditLog]):
    """Репозиторій доступу до записів журналу аудиту."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def get_recent(self, skip: int = 0, limit: int = 100) -> Sequence[AuditLog]:
        """Повертає останні записи журналу аудиту."""
        query = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class SystemBackupRepository(BaseRepository[SystemBackup]):
    """Репозиторій доступу до записів про резервні копії."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SystemBackup, session)

    async def get_recent(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[SystemBackup]:
        """Повертає список резервних копій у зворотному хронологічному порядку."""
        query = (
            select(SystemBackup)
            .order_by(SystemBackup.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
