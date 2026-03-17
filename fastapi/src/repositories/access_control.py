from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.access_rules import AccessRule
from src.models.permissions import Permission
from src.models.resources import Resource
from src.models.roles import Role
from src.models.user_roles import UserRole


class AccessControlRepository:
    """Репозиторий проверки фактических прав доступа пользователя к ресурсу."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def has_permission(
        self,
        user_id: int,
        resource_code: str,
        permission_code: str,
    ) -> bool:
        """Проверяет наличие разрешающего правила для пользователя, ресурса и действия."""

        stmt = (
            select(AccessRule.id)
            .join(Role, Role.id == AccessRule.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .join(Resource, Resource.id == AccessRule.resource_id)
            .join(Permission, Permission.id == AccessRule.permission_id)
            .where(UserRole.user_id == user_id)
            .where(Resource.code == resource_code)
            .where(Permission.code == permission_code)
            .where(AccessRule.is_allowed.is_(True))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

