from typing import Any

from src.models.users import User
from src.repositories.mappers.base import DataMapper
from src.schemas.users import UserCreate, UserRead, UserUpdate


class UsersMapper(DataMapper[User, UserRead]):
    @staticmethod
    def to_schema(orm_obj: User, roles: list[str] | None = None) -> UserRead:
        return UserRead(
            id=orm_obj.id,
            email=orm_obj.email,
            first_name=orm_obj.first_name,
            last_name=orm_obj.last_name,
            middle_name=orm_obj.middle_name,
            is_active=orm_obj.is_active,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
            deleted_at=orm_obj.deleted_at,
            roles=roles or [],
        )

    @staticmethod
    def from_schema(
        schema_obj: UserCreate | UserUpdate,
        exclude: set[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        exclude = exclude or set()
        data = schema_obj.model_dump(exclude=exclude, exclude_unset=True)
        data.update(kwargs)
        return data

