"""Сервісний шар управління тарифними планами."""

import uuid
from collections.abc import Sequence
from datetime import time
from decimal import Decimal

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.tariffs.models import Tariff
from app.modules.tariffs.repository import TariffRepository
from app.modules.tariffs.schemas import TariffCreate, TariffUpdate


class TariffService:
    """Сервіс управління тарифами та розрахунку вартості спожитої енергії."""

    def __init__(self, repo: TariffRepository) -> None:
        self.repo = repo

    async def create_tariff(self, user_id: uuid.UUID, data: TariffCreate) -> Tariff:
        """Створює новий тарифний план для користувача."""
        if data.is_default:
            await self.repo.unset_default_for_user(user_id)
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def list_tariffs(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Tariff]:
        """Повертає список тарифів користувача."""
        return await self.repo.get_by_user(user_id=user_id, skip=skip, limit=limit)

    async def get_user_tariff(self, tariff_id: uuid.UUID, user_id: uuid.UUID) -> Tariff:
        """Отримує тариф за ідентифікатором і перевіряє право власності."""
        tariff = await self.repo.get_by_id(tariff_id)
        if not tariff:
            raise NotFoundException("Tariff not found")
        if tariff.user_id != user_id:
            raise ForbiddenException("Access to this tariff is forbidden")
        return tariff

    async def update_tariff(
        self, tariff_id: uuid.UUID, user_id: uuid.UUID, data: TariffUpdate
    ) -> Tariff:
        """Оновлює існуючий тарифний план."""
        tariff = await self.get_user_tariff(tariff_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_default") is True:
            await self.repo.unset_default_for_user(user_id)
        return await self.repo.update(tariff, **update_data)

    async def delete_tariff(self, tariff_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Видаляє тарифний план користувача."""
        tariff = await self.get_user_tariff(tariff_id, user_id)
        await self.repo.delete(tariff)

    @staticmethod
    def resolve_zone_and_rate(
        tariff: Tariff | None, measurement_time: time
    ) -> tuple[str, Decimal]:
        """Визначає тарифну зону (DAY / NIGHT) та діючу ставку за 1 кВт·год."""
        if tariff is None:
            return "DAY", Decimal("4.3200")

        if not tariff.is_two_zone:
            return "DAY", tariff.day_rate_per_kwh

        start = tariff.night_start_time
        end = tariff.night_end_time
        if start <= end:
            is_night = start <= measurement_time < end
        else:
            is_night = measurement_time >= start or measurement_time < end

        if is_night:
            rate = (tariff.day_rate_per_kwh * tariff.night_multiplier).quantize(
                Decimal("0.0001")
            )
            return "NIGHT", rate
        return "DAY", tariff.day_rate_per_kwh
