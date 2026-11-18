"""Сервіс реєстрації, входу та ротації токенів користувачів."""

import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.users.enums import UserRole, UserStatus
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class AuthService:
    """Сервіс автентифікації та управління JWT-сесіями."""

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def _issue_tokens(self, user: User) -> tuple[str, str]:
        """Випускає нову пару access_token і refresh_token та зберігає хеш у БД."""
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role.value,
                "tier": user.subscription_tier.value,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        token_digest = hash_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.token_repo.create(
            token_hash=token_digest,
            user_id=user.id,
            expires_at=expires_at,
        )
        return access_token, refresh_token

    async def register(self, data: RegisterRequest) -> tuple[User, str, str]:
        """Реєструє нового споживача з хешуванням пароля за алгоритмом Argon2id."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException("User with this email is already registered")

        hashed_pwd = get_password_hash(data.password)
        user = await self.user_repo.create(
            email=data.email.strip().lower(),
            hashed_password=hashed_pwd,
            first_name=data.first_name,
            last_name=data.last_name,
            locale=data.locale,
            timezone=data.timezone,
            role=UserRole.USER,
            is_verified=True,
            is_superuser=False,
        )

        access_token, refresh_token = await self._issue_tokens(user)
        return user, access_token, refresh_token

    async def authenticate(self, data: LoginRequest) -> tuple[User, str, str]:
        """Перевіряє облікові дані та повертає токени доступу."""
        user = await self.user_repo.get_by_email(data.email)
        if not user or not user.hashed_password:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if user.status != UserStatus.ACTIVE or user.is_deleted:
            raise UnauthorizedException("Account is deactivated or banned")

        access_token, refresh_token = await self._issue_tokens(user)
        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token_str: str) -> tuple[User, str, str]:
        """Виконує ротацію refresh_token з інвалідацією попереднього токена."""
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid token")

        token_digest = hash_token(refresh_token_str)
        stored_token = await self.token_repo.get_by_hash(token_digest)
        if not stored_token or stored_token.revoked:
            raise UnauthorizedException("Session expired or token revoked")

        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            await self.token_repo.revoke(stored_token)
            raise UnauthorizedException("Token expired")

        await self.token_repo.revoke(stored_token)

        user_id = uuid.UUID(user_id_str)
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE or user.is_deleted:
            raise UnauthorizedException("User not found or deactivated")

        new_access_token, new_refresh_token = await self._issue_tokens(user)
        return user, new_access_token, new_refresh_token

    async def logout(
        self, refresh_token_str: str | None, user_id: uuid.UUID | None
    ) -> None:
        """Відкликає поточний refresh-токен або всі сесії користувача."""
        if refresh_token_str:
            token_digest = hash_token(refresh_token_str)
            stored_token = await self.token_repo.get_by_hash(token_digest)
            if stored_token:
                await self.token_repo.revoke(stored_token)
        elif user_id:
            await self.token_repo.revoke_all_for_user(user_id)
