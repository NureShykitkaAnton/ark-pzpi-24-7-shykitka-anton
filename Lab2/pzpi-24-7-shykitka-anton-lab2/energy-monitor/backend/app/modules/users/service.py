"""Сервісний шар управління профілями та правами користувачів."""

import uuid
from collections.abc import Sequence

from app.core.exceptions import NotFoundException
from app.core.security import get_password_hash
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserAdminUpdate, UserUpdate


class UserService:
    """Сервіс бізнес-логіки облікових записів користувачів."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Отримує користувача за ідентифікатором або генерує виняток 404."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Повертає список усіх активних користувачів."""
        return await self.user_repo.get_all(skip=skip, limit=limit)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """Оновлює профіль користувача та його налаштування локалізації."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.user_repo.update(user, exclude_none=True, **update_data)

    async def admin_update_user(self, user: User, data: UserAdminUpdate) -> User:
        """Адміністративне оновлення статусу, ролі або рівня підписки користувача."""
        update_data = data.model_dump(exclude_unset=True)
        if "role" in update_data and update_data["role"] == UserRole.ADMIN:
            update_data["is_superuser"] = True
        return await self.user_repo.update(user, exclude_none=True, **update_data)

    async def change_password(self, user: User, new_password: str) -> User:
        """Змінює пароль користувача з хешуванням за алгоритмом Argon2id."""
        hashed_password = get_password_hash(new_password)
        return await self.user_repo.update(user, hashed_password=hashed_password)

    async def delete(self, user: User) -> None:
        """Анонімізує та деактивує обліковий запис користувача."""
        await self.user_repo.soft_delete(user)
