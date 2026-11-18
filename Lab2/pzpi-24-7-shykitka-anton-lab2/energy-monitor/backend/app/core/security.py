"""Модуль криптографічного захисту: хешування Argon2id, генерація JWT та токенів IoT-пристроїв."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

password_hash = PasswordHash((Argon2Hasher(),))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє відповідність відкритого пароля збереженому хешу Argon2id."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Обчислює криптостійкий хеш пароля за алгоритмом Argon2id."""
    return password_hash.hash(password)


def hash_token(raw_token: str) -> str:
    """Обчислює SHA-256 дайджест для безпечного зберігання refresh-токенів та ключів IoT."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_device_api_token() -> str:
    """Генерує криптографічно стійкий API-токен для мікроконтролера ESP32."""
    return f"em_iot_{secrets.token_urlsafe(32)}"


def create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Формує підписаний JWT-токен із унікальним ідентифікатором jti (RFC 7519)."""
    now = datetime.now(UTC)
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Створює короткоживучий JWT access_token для авторизації запитів до API."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=delta,
        additional_claims=additional_claims,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Створює довгоживучий JWT refresh_token для ротації сесії."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=delta,
        additional_claims=additional_claims,
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Декодує та валідує JWT-токен і перевіряє його цільовий тип."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if expected_type and payload.get("type") != expected_type:
            raise UnauthorizedException(
                detail=f"Invalid token type. Expected {expected_type}"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(detail="Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException(detail="Could not validate credentials")
