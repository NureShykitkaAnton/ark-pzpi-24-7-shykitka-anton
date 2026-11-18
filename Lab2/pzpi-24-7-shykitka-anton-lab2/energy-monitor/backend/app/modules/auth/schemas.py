"""Схеми запитів та відповідей модуля автентифікації."""

from pydantic import BaseModel, EmailStr, Field

from app.modules.users.schemas import UserRead


class LoginRequest(BaseModel):
    """Схема вхідних облікових даних при авторизації."""

    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    """Схема даних для реєстрації нового споживача."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    locale: str = Field(default="uk", pattern="^(uk|en)$")
    timezone: str = Field(default="Europe/Kyiv", max_length=64)


class TokenResponse(BaseModel):
    """Схема відповіді із парою JWT-токенів та даними профілю."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: UserRead


class RefreshRequest(BaseModel):
    """Схема запиту на ротацію refresh-токена."""

    refresh_token: str | None = None
