"""Сервісний шар управління лініями живлення та автентифікацією пристроїв ESP32."""

import uuid
from collections.abc import Sequence

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.security import generate_device_api_token, hash_token
from app.modules.lines.models import PowerLine
from app.modules.lines.repository import PowerLineRepository
from app.modules.lines.schemas import PowerLineCreate, PowerLineUpdate


class PowerLineService:
    """Сервіс бізнес-логіки ліній живлення та сенсорних вузлів."""

    def __init__(self, repo: PowerLineRepository) -> None:
        self.repo = repo

    async def create_line(
        self, user_id: uuid.UUID, data: PowerLineCreate
    ) -> tuple[PowerLine, str]:
        """Створює нову лінію живлення та генерує секретний токен для ESP32."""
        normalized_uid = data.device_uid.strip().upper()
        existing = await self.repo.get_by_device_uid(normalized_uid)
        if existing:
            raise ConflictException(
                f"Device with UID '{normalized_uid}' is already registered"
            )

        raw_device_token = generate_device_api_token()
        token_hash = hash_token(raw_device_token)

        payload = data.model_dump()
        payload["device_uid"] = normalized_uid
        line = await self.repo.create(
            user_id=user_id,
            device_token_hash=token_hash,
            **payload,
        )
        return line, raw_device_token

    async def list_lines(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[PowerLine]:
        """Повертає список ліній живлення користувача."""
        return await self.repo.get_by_user(user_id=user_id, skip=skip, limit=limit)

    async def get_user_line(self, line_id: uuid.UUID, user_id: uuid.UUID) -> PowerLine:
        """Отримує лінію живлення та перевіряє належність користувачу."""
        line = await self.repo.get_by_id_with_tariff(line_id)
        if not line:
            raise NotFoundException("Power line not found")
        if line.user_id != user_id:
            raise ForbiddenException("Access to this power line is forbidden")
        return line

    async def update_line(
        self, line_id: uuid.UUID, user_id: uuid.UUID, data: PowerLineUpdate
    ) -> PowerLine:
        """Оновлює конфігурацію лінії живлення."""
        line = await self.get_user_line(line_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(line, exclude_none=False, **update_data)

    async def regenerate_device_token(
        self, line_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[PowerLine, str]:
        """Перевипускає API-токен для мікроконтролера ESP32."""
        line = await self.get_user_line(line_id, user_id)
        raw_device_token = generate_device_api_token()
        token_hash = hash_token(raw_device_token)
        updated = await self.repo.update(line, device_token_hash=token_hash)
        return updated, raw_device_token

    async def delete_line(self, line_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Видаляє лінію живлення разом із пов'язаними даними."""
        line = await self.get_user_line(line_id, user_id)
        await self.repo.delete(line)
