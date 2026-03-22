from pydantic import BaseModel, EmailStr, Field


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
    """Тело запроса для обновления токена доступа."""

    refresh_token: str = Field(
        description="Токен обновления сессии (refresh), выданный при входе или при предыдущем обновлении пары.",
        examples=["refresh_token_value"],
    )


class TokenResponse(BaseModel):
    """Ответ с парой токенов: доступ (JWT) и обновление сессии (refresh)."""

    access_token: str = Field(
        description="JWT токен доступа для авторизации в защищённых ручках.",
        examples=["access_token_value"],
    )
    refresh_token: str = Field(
        description="Токен обновления для получения новой пары токенов.",
        examples=["refresh_token_value"],
    )
    token_type: str = Field(
        default="bearer",
        description="Тип токена авторизации.",
        examples=["bearer"],
    )
