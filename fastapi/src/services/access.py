from fastapi import HTTPException

from src.models.access_rules import AccessRule
from src.repositories.access_admin import AccessAdminRepository
from src.schemas.access import (
    AccessRuleCreate,
    AccessRuleRead,
    AccessRuleUpdate,
    PermissionRead,
    ResourceRead,
    RoleRead,
)


class AccessAdminService:
    """Сервис административного управления ролями и правилами доступа."""

    def __init__(self, repository: AccessAdminRepository) -> None:
        self.repository = repository

    def _build_rule_read(
        self,
        rule: AccessRule,
        role_name: str,
        resource_code: str,
        permission_code: str,
    ) -> AccessRuleRead:
        """Преобразует ORM-правило в DTO для ответа API."""

        return AccessRuleRead(
            id=rule.id,
            role_id=rule.role_id,
            role_name=role_name,
            resource_id=rule.resource_id,
            resource_code=resource_code,
            permission_id=rule.permission_id,
            permission_code=permission_code,
            is_allowed=rule.is_allowed,
        )

    async def list_roles(self) -> list[RoleRead]:
        """Возвращает список ролей в формате API."""

        roles = await self.repository.list_roles()
        return [RoleRead(id=role.id, name=role.name, description=role.description) for role in roles]

    async def list_resources(self) -> list[ResourceRead]:
        """Возвращает список ресурсов в формате API."""

        resources = await self.repository.list_resources()
        return [
            ResourceRead(
                id=resource.id,
                code=resource.code,
                description=resource.description,
            )
            for resource in resources
        ]

    async def list_permissions(self) -> list[PermissionRead]:
        """Возвращает список действий в формате API."""

        permissions = await self.repository.list_permissions()
        return [
            PermissionRead(
                id=permission.id,
                code=permission.code,
                description=permission.description,
            )
            for permission in permissions
        ]

    async def list_rules(self) -> list[AccessRuleRead]:
        """Возвращает список правил доступа в формате API."""

        rows = await self.repository.list_rules()
        return [
            self._build_rule_read(rule, role_name, resource_code, permission_code)
            for rule, role_name, resource_code, permission_code in rows
        ]

    async def create_rule(self, data: AccessRuleCreate) -> AccessRuleRead:
        """
        Создает новое правило доступа.

        Raises:
            HTTPException: 404 если роль, ресурс или действие не найдены.
            HTTPException: 409 если правило уже существует.
            HTTPException: 500 если не удалось собрать DTO ответа.
        """

        if not await self.repository.role_exists(data.role_id):
            raise HTTPException(status_code=404, detail="Role not found")
        if not await self.repository.resource_exists(data.resource_id):
            raise HTTPException(status_code=404, detail="Resource not found")
        if not await self.repository.permission_exists(data.permission_id):
            raise HTTPException(status_code=404, detail="Permission not found")

        existing = await self.repository.find_rule(
            role_id=data.role_id,
            resource_id=data.resource_id,
            permission_id=data.permission_id,
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="Access rule already exists")

        rule = AccessRule(
            role_id=data.role_id,
            resource_id=data.resource_id,
            permission_id=data.permission_id,
            is_allowed=data.is_allowed,
        )
        rule = await self.repository.add_rule(rule)
        await self.repository.commit()

        rows = await self.repository.list_rules()
        for row in rows:
            current_rule, role_name, resource_code, permission_code = row
            if current_rule.id == rule.id:
                return self._build_rule_read(
                    current_rule,
                    role_name,
                    resource_code,
                    permission_code,
                )

        raise HTTPException(status_code=500, detail="Failed to build access rule response")

    async def update_rule(self, rule_id: int, data: AccessRuleUpdate) -> AccessRuleRead:
        """
        Изменяет существующее правило доступа.

        Raises:
            HTTPException: 404 если правило не найдено.
            HTTPException: 500 если не удалось собрать DTO ответа.
        """

        rule = await self.repository.get_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Access rule not found")

        rule.is_allowed = data.is_allowed
        await self.repository.commit()

        rows = await self.repository.list_rules()
        for row in rows:
            current_rule, role_name, resource_code, permission_code = row
            if current_rule.id == rule.id:
                return self._build_rule_read(
                    current_rule,
                    role_name,
                    resource_code,
                    permission_code,
                )

        raise HTTPException(status_code=500, detail="Failed to build access rule response")

    async def delete_rule(self, rule_id: int) -> None:
        """
        Удаляет правило доступа.

        Raises:
            HTTPException: 404 если правило не найдено.
        """

        rule = await self.repository.get_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Access rule not found")
        await self.repository.delete_rule(rule)
        await self.repository.commit()
