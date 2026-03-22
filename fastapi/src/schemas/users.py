from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Базовая схема пользователя с общими полями профиля."""

    email: EmailStr = Field(
        description="Email пользователя. Используется как логин.",
        examples=["user@em.ru"],
    )
    first_name: str | None = Field(
        default=None,
        description="Имя пользователя.",
        examples=["Иван"],
    )
    last_name: str | None = Field(
        default=None,
        description="Фамилия пользователя.",
        examples=["Иванов"],
    )
    middle_name: str | None = Field(
        default=None,
        description="Отчество пользователя.",
        examples=["Иванович"],
    )


class UserCreate(UserBase):
    """Тело запроса на регистрацию пользователя."""

    password: str = Field(
        min_length=8,
        max_length=72,
        description="Пароль пользователя. Хешируется перед сохранением.",
        examples=["test_password"],
    )
    password_confirm: str = Field(
        min_length=8,
        max_length=72,
        description="Повтор пароля для проверки совпадения.",
        examples=["test_password"],
    )


class UserUpdate(BaseModel):
    """Тело запроса на частичное обновление профиля пользователя."""

    email: EmailStr | None = Field(
        default=None,
        description="Новый email пользователя.",
        examples=["updated@em.ru"],
    )
    first_name: str | None = Field(
        default=None,
        description="Новое имя пользователя.",
        examples=["Петр"],
    )
    last_name: str | None = Field(
        default=None,
        description="Новая фамилия пользователя.",
        examples=["Петров"],
    )
    middle_name: str | None = Field(
        default=None,
        description="Новое отчество пользователя.",
        examples=["Петрович"],
    )


class UserRead(UserBase):
    """Схема пользователя в ответах API."""

    id: int = Field(description="Идентификатор пользователя.", examples=[1])
    is_active: bool = Field(description="Признак активности учетной записи.", examples=[True])
    created_at: datetime = Field(description="Дата и время создания пользователя.")
    updated_at: datetime = Field(description="Дата и время последнего обновления пользователя.")
    deleted_at: datetime | None = Field(
        default=None,
        description="Дата и время мягкого удаления пользователя, если аккаунт деактивирован.",
    )
    roles: list[str] = Field(
        default_factory=list,
        description="Список ролей пользователя в системе доступа.",
        examples=[["user"]],
    )

    model_config = ConfigDict(from_attributes=True)
