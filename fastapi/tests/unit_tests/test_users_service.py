from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.schemas.users import UserCreate, UserUpdate
from src.services.users import UserService
from src.utils.auth import RequestUser


def make_user(
    user_id: int,
    email: str = "user@em.ru",
    *,
    deleted_at=None,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=user_id,
        email=email,
        first_name="Test",
        last_name="User",
        middle_name=None,
        password_hash="hashed",
        deleted_at=deleted_at,
        is_active=is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def make_repository():
    repository = SimpleNamespace()
    repository.session = object()
    repository.get_by_id = AsyncMock()
    repository.get_by_email = AsyncMock()
    repository.get_role_names = AsyncMock(return_value=[])
    repository.list_active_users = AsyncMock(return_value=[])
    repository.add = AsyncMock()
    repository.commit = AsyncMock()
    repository.get_role_by_name = AsyncMock()
    repository.add_user_role = AsyncMock()
    repository.remove_user_role = AsyncMock(return_value=True)
    return repository


def make_actor(user_id: int, roles: list[str]) -> RequestUser:
    return RequestUser(user=make_user(user_id, email=f"user{user_id}@em.ru"), roles=roles)


@pytest.mark.asyncio
async def test_build_user_read_uses_repository_roles():
    repository = make_repository()
    repository.get_role_names.return_value = ["admin", "user"]
    service = UserService(repository)

    result = await service._build_user_read(make_user(30, email="mapper@em.ru"))

    assert result.email == "mapper@em.ru"
    assert result.roles == ["admin", "user"]


@pytest.mark.asyncio
async def test_get_target_or_404_returns_user():
    repository = make_repository()
    repository.get_by_id.return_value = make_user(1)
    service = UserService(repository)

    result = await service._get_target_or_404(1)

    assert result.id == 1


@pytest.mark.asyncio
async def test_get_target_or_404_raises_for_missing_or_deleted_user():
    repository = make_repository()
    service = UserService(repository)

    repository.get_by_id.return_value = None
    with pytest.raises(HTTPException) as missing_exc:
        await service._get_target_or_404(1)

    repository.get_by_id.return_value = make_user(2, deleted_at=datetime.utcnow())
    with pytest.raises(HTTPException) as deleted_exc:
        await service._get_target_or_404(2)

    assert missing_exc.value.status_code == 404
    assert deleted_exc.value.detail == "User not found"


@pytest.mark.asyncio
async def test_ensure_email_is_free_skips_none_and_same_user():
    repository = make_repository()
    repository.get_by_email.return_value = make_user(10, email="same@em.ru")
    service = UserService(repository)

    await service._ensure_email_is_free(None)
    await service._ensure_email_is_free("same@em.ru", current_user_id=10)


@pytest.mark.asyncio
async def test_ensure_email_is_free_raises_for_duplicate():
    repository = make_repository()
    repository.get_by_email.return_value = make_user(11, email="busy@em.ru")
    service = UserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service._ensure_email_is_free("busy@em.ru", current_user_id=99)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User with this email already exists"


@pytest.mark.asyncio
async def test_can_view_user_handles_role_matrix():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(2)

    assert await service._can_view_user(make_actor(2, ["user"]), target) is True
    assert await service._can_view_user(make_actor(1, ["superadmin"]), target) is True
    assert await service._can_view_user(make_actor(1, ["admin"]), target) is True

    repository.get_role_names.return_value = ["user"]
    assert await service._can_view_user(make_actor(1, ["manager"]), target) is True

    repository.get_role_names.return_value = ["admin"]
    assert await service._can_view_user(make_actor(1, ["manager"]), target) is False
    assert await service._can_view_user(make_actor(1, ["user"]), target) is False


@pytest.mark.asyncio
async def test_ensure_can_update_user_allows_self_and_superadmin():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(7)

    await service._ensure_can_update_user(make_actor(7, ["user"]), target)
    await service._ensure_can_update_user(make_actor(1, ["superadmin"]), target)


@pytest.mark.asyncio
async def test_ensure_can_update_user_blocks_admin_target_and_regular_user():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(8)

    repository.get_role_names.return_value = ["admin"]
    with pytest.raises(HTTPException) as admin_exc:
        await service._ensure_can_update_user(make_actor(1, ["admin"]), target)

    with pytest.raises(HTTPException) as user_exc:
        await service._ensure_can_update_user(make_actor(1, ["user"]), target)

    assert admin_exc.value.detail == "Admins cannot update other admins or superadmins"
    assert user_exc.value.detail == "You cannot update this user"


@pytest.mark.asyncio
async def test_ensure_can_update_user_allows_admin_for_non_admin_target():
    repository = make_repository()
    repository.get_role_names.return_value = ["user"]
    service = UserService(repository)

    await service._ensure_can_update_user(make_actor(1, ["admin"]), make_user(8))


@pytest.mark.asyncio
async def test_ensure_can_delete_user_handles_role_rules():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(20)

    with pytest.raises(HTTPException) as superadmin_self_exc:
        await service._ensure_can_delete_user(make_actor(20, ["superadmin"]), target)
    assert superadmin_self_exc.value.detail == "Superadmin cannot delete themselves"

    await service._ensure_can_delete_user(make_actor(1, ["superadmin"]), target)
    await service._ensure_can_delete_user(make_actor(20, ["admin"]), target)
    await service._ensure_can_delete_user(make_actor(20, ["user"]), target)

    repository.get_role_names.return_value = ["admin"]
    with pytest.raises(HTTPException) as admin_target_exc:
        await service._ensure_can_delete_user(make_actor(1, ["admin"]), target)
    assert admin_target_exc.value.detail == "Admins cannot delete other admins or superadmins"

    with pytest.raises(HTTPException) as forbidden_exc:
        await service._ensure_can_delete_user(make_actor(1, ["manager"]), target)
    assert forbidden_exc.value.detail == "You cannot delete this user"


@pytest.mark.asyncio
async def test_ensure_can_delete_user_allows_admin_for_non_admin_target():
    repository = make_repository()
    repository.get_role_names.return_value = ["user"]
    service = UserService(repository)

    await service._ensure_can_delete_user(make_actor(1, ["admin"]), make_user(20))


@pytest.mark.asyncio
async def test_register_user_raises_when_passwords_do_not_match():
    repository = make_repository()
    service = UserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(
            UserCreate(
                email="user@em.ru",
                password="one12345",
                password_confirm="two12345",
                first_name="A",
                last_name="B",
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Passwords do not match"


@pytest.mark.asyncio
async def test_register_user_creates_user(monkeypatch):
    repository = make_repository()
    repository.get_by_email.return_value = None
    created_user = make_user(15, email="new@em.ru")
    repository.add.return_value = created_user
    service = UserService(repository)

    monkeypatch.setattr("src.services.users.hash_password", lambda password: f"hash:{password}")
    service._build_user_read = AsyncMock(return_value=SimpleNamespace(email="new@em.ru"))

    payload = UserCreate(
        email="new@em.ru",
        password="secret123",
        password_confirm="secret123",
        first_name="New",
        last_name="User",
    )
    result = await service.register_user(payload)

    assert result.email == "new@em.ru"
    repository.add.assert_awaited_once()
    saved_user = repository.add.await_args.args[0]
    assert saved_user.password_hash == "hash:secret123"
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_me_builds_read_model():
    repository = make_repository()
    service = UserService(repository)
    actor = make_actor(3, ["user"])
    service._build_user_read = AsyncMock(return_value="me-read")

    result = await service.get_me(actor)

    assert result == "me-read"
    service._build_user_read.assert_awaited_once_with(actor.user)


@pytest.mark.asyncio
async def test_get_user_raises_when_actor_cannot_view_target():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(4)
    service._get_target_or_404 = AsyncMock(return_value=target)
    service._can_view_user = AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user(make_actor(1, ["user"]), 4)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You cannot view this user"


@pytest.mark.asyncio
async def test_get_user_returns_read_model_when_allowed():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(5)
    service._get_target_or_404 = AsyncMock(return_value=target)
    service._can_view_user = AsyncMock(return_value=True)
    service._build_user_read = AsyncMock(return_value="target-read")

    result = await service.get_user(make_actor(1, ["admin"]), 5)

    assert result == "target-read"


@pytest.mark.asyncio
async def test_list_users_returns_only_visible_users():
    repository = make_repository()
    repository.list_active_users.return_value = [make_user(1), make_user(2), make_user(3)]
    service = UserService(repository)
    service._can_view_user = AsyncMock(side_effect=[True, False, True])
    service._build_user_read = AsyncMock(side_effect=["u1", "u3"])

    result = await service.list_users(make_actor(99, ["manager"]))

    assert result == ["u1", "u3"]


@pytest.mark.asyncio
async def test_update_user_updates_fields_and_returns_refreshed_model():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(9, email="old@em.ru")
    refreshed = make_user(9, email="new@em.ru")
    service._get_target_or_404 = AsyncMock(side_effect=[target, refreshed])
    service._ensure_can_update_user = AsyncMock()
    service._ensure_email_is_free = AsyncMock()
    service._build_user_read = AsyncMock(return_value="updated-read")

    result = await service.update_user(
        make_actor(1, ["admin"]),
        9,
        UserUpdate(email="new@em.ru", first_name="Updated"),
    )

    assert result == "updated-read"
    assert target.email == "new@em.ru"
    assert target.first_name == "Updated"
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_soft_delete_user_marks_user_inactive_and_revokes_tokens():
    repository = make_repository()
    service = UserService(repository)
    service.refresh_token_repository = SimpleNamespace(
        revoke_all_user_tokens=AsyncMock()
    )
    target = make_user(12)
    service._get_target_or_404 = AsyncMock(return_value=target)
    service._ensure_can_delete_user = AsyncMock()

    await service.soft_delete_user(make_actor(1, ["admin"]), 12)

    assert target.is_active is False
    assert target.deleted_at is not None
    service.refresh_token_repository.revoke_all_user_tokens.assert_awaited_once_with(12)
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_can_manage_roles_allows_superadmin_and_admin_for_regular_users():
    repository = make_repository()
    service = UserService(repository)
    target = make_user(30)

    # superadmin может управлять ролями любого обычного пользователя
    await service._ensure_can_manage_roles(
        make_actor(1, ["superadmin"]),
        target,
        "admin",
    )

    # admin может управлять ролями обычного пользователя
    repository.get_role_names.return_value = ["user"]
    await service._ensure_can_manage_roles(
        make_actor(2, ["admin"]),
        target,
        "manager",
    )


@pytest.mark.asyncio
async def test_ensure_can_manage_roles_enforces_hierarchy_rules():
    repository = make_repository()
    service = UserService(repository)
    target_admin = make_user(40)
    target_superadmin = make_user(41)

    # Обычный пользователь не может управлять ролями
    with pytest.raises(HTTPException) as user_exc:
        await service._ensure_can_manage_roles(
            make_actor(3, ["user"]),
            target_admin,
            "user",
        )

    # admin не может управлять ролями superadmin
    repository.get_role_names.return_value = ["superadmin"]
    with pytest.raises(HTTPException) as admin_vs_super_exc:
        await service._ensure_can_manage_roles(
            make_actor(2, ["admin"]),
            target_superadmin,
            "user",
        )

    # admin не может управлять ролью superadmin
    repository.get_role_names.return_value = []
    with pytest.raises(HTTPException) as admin_set_super_exc:
        await service._ensure_can_manage_roles(
            make_actor(2, ["admin"]),
            target_admin,
            "superadmin",
        )

    # admin не может управлять другим admin
    repository.get_role_names.return_value = ["admin"]
    with pytest.raises(HTTPException) as admin_vs_admin_exc:
        await service._ensure_can_manage_roles(
            make_actor(2, ["admin"]),
            target_admin,
            "user",
        )

    assert user_exc.value.status_code == 403
    assert admin_vs_super_exc.value.status_code == 403
    assert admin_set_super_exc.value.status_code == 403
    assert admin_vs_admin_exc.value.status_code == 403


@pytest.mark.asyncio
async def test_assign_role_adds_role_and_returns_updated_user():
    repository = make_repository()
    target = make_user(50)
    refreshed = make_user(50)
    repository.get_role_by_name.return_value = SimpleNamespace(id=7, name="manager")
    service = UserService(repository)
    service._get_target_or_404 = AsyncMock(side_effect=[target, refreshed])
    service._ensure_can_manage_roles = AsyncMock()
    service._build_user_read = AsyncMock(return_value="user-with-role")

    result = await service.assign_role(
        make_actor(1, ["superadmin"]),
        user_id=50,
        role_name="manager",
    )

    assert result == "user-with-role"
    service._ensure_can_manage_roles.assert_awaited_once()
    repository.get_role_by_name.assert_awaited_once()
    repository.add_user_role.assert_awaited_once_with(50, 7)
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_role_raises_when_role_not_found():
    repository = make_repository()
    target = make_user(51)
    repository.get_role_by_name.return_value = None
    service = UserService(repository)
    service._get_target_or_404 = AsyncMock(return_value=target)
    service._ensure_can_manage_roles = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await service.assign_role(
            make_actor(1, ["superadmin"]),
            user_id=51,
            role_name="unknown",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Role not found"


@pytest.mark.asyncio
async def test_remove_role_deletes_link_and_returns_updated_user():
    repository = make_repository()
    target = make_user(60)
    refreshed = make_user(60)
    repository.get_role_by_name.return_value = SimpleNamespace(id=3, name="user")
    repository.remove_user_role.return_value = True
    service = UserService(repository)
    service._get_target_or_404 = AsyncMock(side_effect=[target, refreshed])
    service._ensure_can_manage_roles = AsyncMock()
    service._build_user_read = AsyncMock(return_value="user-without-role")

    result = await service.remove_role(
        make_actor(1, ["superadmin"]),
        user_id=60,
        role_name="user",
    )

    assert result == "user-without-role"
    repository.remove_user_role.assert_awaited_once_with(60, 3)
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_role_raises_when_user_does_not_have_role():
    repository = make_repository()
    target = make_user(61)
    repository.get_role_by_name.return_value = SimpleNamespace(id=4, name="manager")
    repository.remove_user_role.return_value = False
    service = UserService(repository)
    service._get_target_or_404 = AsyncMock(return_value=target)
    service._ensure_can_manage_roles = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await service.remove_role(
            make_actor(1, ["superadmin"]),
            user_id=61,
            role_name="manager",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User does not have this role"
