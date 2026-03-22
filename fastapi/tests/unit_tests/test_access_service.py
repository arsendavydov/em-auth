from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.schemas.access import AccessRuleCreate, AccessRuleUpdate
from src.services.access import AccessAdminService


def make_repository():
    repository = SimpleNamespace()
    repository.list_roles = AsyncMock(return_value=[])
    repository.list_resources = AsyncMock(return_value=[])
    repository.list_permissions = AsyncMock(return_value=[])
    repository.list_rules = AsyncMock(return_value=[])
    repository.get_rule = AsyncMock(return_value=None)
    repository.role_exists = AsyncMock(return_value=True)
    repository.resource_exists = AsyncMock(return_value=True)
    repository.permission_exists = AsyncMock(return_value=True)
    repository.find_rule = AsyncMock(return_value=None)
    repository.add_rule = AsyncMock()
    repository.delete_rule = AsyncMock()
    repository.commit = AsyncMock()
    return repository


@pytest.mark.asyncio
async def test_list_methods_map_entities_to_read_models():
    repository = make_repository()
    repository.list_roles.return_value = [SimpleNamespace(id=1, name="admin", description="a")]
    repository.list_resources.return_value = [SimpleNamespace(id=2, code="mock:projects:list", description="r")]
    repository.list_permissions.return_value = [SimpleNamespace(id=3, code="read", description="p")]
    rule = SimpleNamespace(
        id=4,
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    repository.list_rules.return_value = [(rule, "admin", "mock:projects:list", "read")]
    service = AccessAdminService(repository)

    roles = await service.list_roles()
    resources = await service.list_resources()
    permissions = await service.list_permissions()
    rules = await service.list_rules()

    assert roles[0].name == "admin"
    assert resources[0].code == "mock:projects:list"
    assert permissions[0].code == "read"
    assert rules[0].resource_code == "mock:projects:list"


@pytest.mark.asyncio
async def test_create_rule_returns_created_rule():
    repository = make_repository()
    created_rule = SimpleNamespace(
        id=7,
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    repository.add_rule.return_value = created_rule
    repository.list_rules.return_value = [(created_rule, "user", "mock:reports:list", "read")]

    service = AccessAdminService(repository)

    result = await service.create_rule(
        AccessRuleCreate(
            role_id=1,
            resource_id=2,
            permission_id=3,
            is_allowed=True,
        )
    )

    assert result.id == 7
    assert result.role_name == "user"
    assert result.resource_code == "mock:reports:list"
    assert result.permission_code == "read"
    assert result.is_allowed is True
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_rule_raises_when_role_not_found():
    repository = make_repository()
    repository.role_exists.return_value = False
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rule(AccessRuleCreate(role_id=1, resource_id=2, permission_id=3, is_allowed=True))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Role not found"


@pytest.mark.asyncio
async def test_create_rule_raises_when_resource_not_found():
    repository = make_repository()
    repository.resource_exists.return_value = False
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rule(AccessRuleCreate(role_id=1, resource_id=2, permission_id=3, is_allowed=True))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Resource not found"


@pytest.mark.asyncio
async def test_create_rule_raises_when_permission_not_found():
    repository = make_repository()
    repository.permission_exists.return_value = False
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rule(AccessRuleCreate(role_id=1, resource_id=2, permission_id=3, is_allowed=True))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Permission not found"


@pytest.mark.asyncio
async def test_create_rule_raises_when_duplicate_exists():
    repository = make_repository()
    repository.find_rule.return_value = SimpleNamespace(id=1)
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rule(AccessRuleCreate(role_id=1, resource_id=2, permission_id=3, is_allowed=True))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Access rule already exists"


@pytest.mark.asyncio
async def test_create_rule_raises_when_response_row_is_missing():
    repository = make_repository()
    repository.add_rule.return_value = SimpleNamespace(
        id=7,
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    repository.list_rules.return_value = []
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rule(AccessRuleCreate(role_id=1, resource_id=2, permission_id=3, is_allowed=True))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to build access rule response"


@pytest.mark.asyncio
async def test_update_rule_returns_updated_rule():
    repository = make_repository()
    existing_rule = SimpleNamespace(
        id=5,
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    repository.get_rule.return_value = existing_rule
    repository.list_rules.return_value = [(existing_rule, "user", "mock:reports:list", "read")]
    service = AccessAdminService(repository)

    result = await service.update_rule(5, AccessRuleUpdate(is_allowed=False))

    assert result.id == 5
    assert result.is_allowed is False
    assert existing_rule.is_allowed is False
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_rule_raises_when_not_found():
    repository = make_repository()
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_rule(5, AccessRuleUpdate(is_allowed=False))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Access rule not found"


@pytest.mark.asyncio
async def test_update_rule_raises_when_response_row_is_missing():
    repository = make_repository()
    repository.get_rule.return_value = SimpleNamespace(
        id=5,
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    repository.list_rules.return_value = []
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_rule(5, AccessRuleUpdate(is_allowed=False))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to build access rule response"


@pytest.mark.asyncio
async def test_delete_rule_raises_when_not_found():
    repository = make_repository()
    service = AccessAdminService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_rule(99)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Access rule not found"


@pytest.mark.asyncio
async def test_delete_rule_deletes_and_commits():
    repository = make_repository()
    existing_rule = SimpleNamespace(id=9)
    repository.get_rule.return_value = existing_rule
    service = AccessAdminService(repository)

    await service.delete_rule(9)

    repository.delete_rule.assert_awaited_once_with(existing_rule)
    repository.commit.assert_awaited_once()
