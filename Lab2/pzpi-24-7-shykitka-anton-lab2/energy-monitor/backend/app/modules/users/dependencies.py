"""Залежності FastAPI для модуля користувачів."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


def get_user_repository(session: SessionDep) -> UserRepository:
    """Фабрика репозиторію користувачів."""
    return UserRepository(session)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Фабрика сервісу користувачів."""
    return UserService(user_repo)
