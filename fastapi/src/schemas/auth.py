from pydantic import BaseModel, EmailStr, Field

from src.schemas.common import MessageResponse


class LoginRequest(BaseModel):
    """Тело запроса для входа пользователя."""

    email: EmailStr = Field(
        description="Email пользователя для входа в систему.",
        examples=["user@em.ru"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Пароль пользователя в открытом виде. Передается только при входе.",
        examples=["test_password"],
    )


class RefreshTokenRequest(BaseModel):
    """Тело запроса для обновления access token."""

    refresh_token: str = Field(
        description="Refresh token, выданный при login или предыдущем refresh.",
        examples=["refresh_token_value"],
    )


class TokenResponse(BaseModel):
    """Ответ с парой access и refresh токенов."""

    access_token: str = Field(
        description="JWT access token для авторизации в защищенных ручках.",
        examples=["access_token_value"],
    )
    refresh_token: str = Field(
        description="Refresh token для получения новой пары токенов.",
        examples=["refresh_token_value"],
    )
    token_type: str = Field(
        default="bearer",
        description="Тип токена авторизации.",
        examples=["bearer"],
    )

