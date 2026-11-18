"""Узагальнений базовий репозиторій для виконання асинхронних CRUD-операцій з базою даних."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Base


class BaseRepository[ModelType: Base]:
    """Базовий клас репозиторію за шаблоном проектування Repository."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> ModelType | None:
        """Повертає запис за первинним ключем або None, якщо запис відсутній."""
        return await self.session.get(self.model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Повертає список записів із підтримкою пагінації (skip, limit)."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        """Створює новий екземпляр моделі у поточній сесії БД та оновлює його стан."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(
        self, db_obj: ModelType, *, exclude_none: bool = True, **kwargs: Any
    ) -> ModelType:
        """Частково або повністю оновлює поля існуючого об'єкта моделі."""
        for key, value in kwargs.items():
            if hasattr(db_obj, key) and not (exclude_none and value is None):
                setattr(db_obj, key, value)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Фізично видаляє переданий об'єкт із бази даних."""
        await self.session.delete(db_obj)
        await self.session.flush()
