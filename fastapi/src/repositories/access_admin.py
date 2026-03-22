"""
CRUD справочников RBAC и правил для админов (не путать с AccessControlRepository.has_permission).

Здесь полные списки и изменение правил; проверка «может ли пользователь X» — в access_control.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.access_rules import AccessRule
from src.models.permissions import Permission
from src.models.resources import Resource
from src.models.roles import Role


class AccessAdminRepository:
    """Репозиторий административных операций с RBAC-справочниками и правилами доступа."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_roles(self) -> list[Role]:
        """Возвращает список ролей, отсортированных по идентификатору."""

        result = await self.session.execute(select(Role).order_by(Role.id))
        return list(result.scalars().all())

    async def list_resources(self) -> list[Resource]:
        """Возвращает список ресурсов, отсортированных по идентификатору."""

        result = await self.session.execute(select(Resource).order_by(Resource.id))
        return list(result.scalars().all())

    async def list_permissions(self) -> list[Permission]:
        """Возвращает список действий, отсортированных по идентификатору."""

        result = await self.session.execute(select(Permission).order_by(Permission.id))
        return list(result.scalars().all())

    async def list_rules(self) -> list[tuple[AccessRule, str, str, str]]:
        """Возвращает список правил доступа вместе с именем роли и кодами ресурса/действия."""

        stmt = (
            select(AccessRule, Role.name, Resource.code, Permission.code)
            .join(Role, Role.id == AccessRule.role_id)
            .join(Resource, Resource.id == AccessRule.resource_id)
            .join(Permission, Permission.id == AccessRule.permission_id)
            .order_by(AccessRule.id)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_rule(self, rule_id: int) -> AccessRule | None:
        """Возвращает правило доступа по идентификатору."""

        result = await self.session.execute(select(AccessRule).where(AccessRule.id == rule_id))
        return result.scalar_one_or_none()

    async def role_exists(self, role_id: int) -> bool:
        """Проверяет существование роли по идентификатору."""

        result = await self.session.execute(select(Role.id).where(Role.id == role_id))
        return result.scalar_one_or_none() is not None

    async def resource_exists(self, resource_id: int) -> bool:
        """Проверяет существование ресурса по идентификатору."""

        result = await self.session.execute(select(Resource.id).where(Resource.id == resource_id))
        return result.scalar_one_or_none() is not None

    async def permission_exists(self, permission_id: int) -> bool:
        """Проверяет существование действия по идентификатору."""

        result = await self.session.execute(select(Permission.id).where(Permission.id == permission_id))
        return result.scalar_one_or_none() is not None

    async def find_rule(
        self,
        role_id: int,
        resource_id: int,
        permission_id: int,
    ) -> AccessRule | None:
        """Ищет существующее правило доступа по составному ключу роль/ресурс/действие."""

        result = await self.session.execute(
            select(AccessRule)
            .where(AccessRule.role_id == role_id)
            .where(AccessRule.resource_id == resource_id)
            .where(AccessRule.permission_id == permission_id)
        )
        return result.scalar_one_or_none()

    async def add_rule(self, rule: AccessRule) -> AccessRule:
        """Добавляет правило доступа и возвращает обновленный ORM-объект."""

        self.session.add(rule)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule: AccessRule) -> None:
        """Удаляет правило доступа из сессии."""

        await self.session.delete(rule)

    async def commit(self) -> None:
        """Фиксирует текущую транзакцию."""

        await self.session.commit()
