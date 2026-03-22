from pydantic import BaseModel, Field


class RoleRead(BaseModel):
    """Схема роли в ответах admin API."""

    id: int = Field(description="Идентификатор роли.", examples=[1])
    name: str = Field(description="Системное имя роли.", examples=["admin"])
    description: str | None = Field(
        default=None,
        description="Человекочитаемое описание роли.",
        examples=["Администратор системы"],
    )


class ResourceRead(BaseModel):
    """Схема ресурса в ответах admin API."""

    id: int = Field(description="Идентификатор ресурса.", examples=[1])
    code: str = Field(description="Код ресурса, используемый в правилах доступа.", examples=["mock:projects:list"])
    description: str | None = Field(
        default=None,
        description="Описание ресурса.",
        examples=["Список mock-проектов"],
    )


class PermissionRead(BaseModel):
    """Схема permission в ответах admin API."""

    id: int = Field(description="Идентификатор действия (permission) в БД.", examples=[1])
    code: str = Field(description="Код действия в системе доступа.", examples=["read"])
    description: str | None = Field(
        default=None,
        description="Описание действия.",
        examples=["Чтение ресурса"],
    )


class AccessRuleCreate(BaseModel):
    """Тело запроса для создания правила доступа."""

    role_id: int = Field(description="Идентификатор роли, для которой создается правило.", examples=[1])
    resource_id: int = Field(description="Идентификатор ресурса, к которому применяется правило.", examples=[2])
    permission_id: int = Field(
        description="Идентификатор действия, разрешаемого или запрещаемого правилом.", examples=[3]
    )
    is_allowed: bool = Field(
        default=True,
        description="Флаг разрешения доступа. `true` разрешает действие, `false` запрещает.",
        examples=[True],
    )


class AccessRuleUpdate(BaseModel):
    """Тело запроса для изменения существующего правила доступа."""

    is_allowed: bool = Field(
        description="Новое состояние правила доступа.",
        examples=[False],
    )


class AccessRuleRead(BaseModel):
    """Схема правила доступа в ответах admin API."""

    id: int = Field(description="Идентификатор правила доступа.", examples=[10])
    role_id: int = Field(description="Идентификатор роли.", examples=[1])
    role_name: str = Field(description="Системное имя роли.", examples=["user"])
    resource_id: int = Field(description="Идентификатор ресурса.", examples=[2])
    resource_code: str = Field(description="Код ресурса.", examples=["mock:reports:list"])
    permission_id: int = Field(description="Идентификатор действия.", examples=[3])
    permission_code: str = Field(description="Код действия.", examples=["read"])
    is_allowed: bool = Field(description="Флаг разрешения доступа.", examples=[True])
