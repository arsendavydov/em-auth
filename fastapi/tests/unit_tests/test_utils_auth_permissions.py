from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt import InvalidTokenError

from src.utils.auth import (
    RequestUser,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    get_current_user,
    get_refresh_token_expires_at,
    require_admin_user,
)
from src.utils.permissions import require_permission


def make_actor(user_id: int = 1, roles: list[str] | None = None) -> RequestUser:
    return RequestUser(
        user=SimpleNamespace(id=user_id, is_active=True, deleted_at=None),
        roles=roles or ["user"],
    )


@pytest.mark.asyncio
async def test_request_user_helpers_and_token_roundtrip():
    actor = make_actor(7, ["admin"])
    token = create_access_token(user_id=7, roles=["admin"])
    decoded = decode_access_token(token)

    assert actor.id == 7
    assert actor.has_role("admin") is True
    assert actor.has_role("user") is False
    assert decoded["sub"] == "7"
    assert decoded["roles"] == ["admin"]


@pytest.mark.asyncio
async def test_refresh_token_helpers_return_expected_values():
    before = datetime.now(timezone.utc)
    token = generate_refresh_token()
    expires_at = get_refresh_token_expires_at()
    after = datetime.now(timezone.utc) + timedelta(days=6)

    assert isinstance(token, str)
    assert len(token) >= 20
    assert expires_at > before
    assert expires_at > after


@pytest.mark.asyncio
async def test_get_current_user_raises_without_bearer_credentials():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None, db=object())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication credentials were not provided"


@pytest.mark.asyncio
async def test_get_current_user_raises_for_invalid_token(monkeypatch):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    monkeypatch.setattr(
        "src.utils.auth.decode_access_token",
        lambda _token: (_ for _ in ()).throw(InvalidTokenError("bad")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=object())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication token"


@pytest.mark.asyncio
async def test_get_current_user_raises_for_unavailable_user(monkeypatch):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="ok-token")
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=SimpleNamespace(id=1, is_active=False, deleted_at=None)),
        get_role_names=AsyncMock(return_value=[]),
    )
    monkeypatch.setattr("src.utils.auth.decode_access_token", lambda _token: {"sub": "1"})
    monkeypatch.setattr("src.utils.auth.UserRepository", lambda _db: repository)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=object())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User is not available"


@pytest.mark.asyncio
async def test_get_current_user_returns_request_user(monkeypatch):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="ok-token")
    user = SimpleNamespace(id=2, is_active=True, deleted_at=None)
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
        get_role_names=AsyncMock(return_value=["manager"]),
    )
    monkeypatch.setattr("src.utils.auth.decode_access_token", lambda _token: {"sub": "2"})
    monkeypatch.setattr("src.utils.auth.UserRepository", lambda _db: repository)

    result = await get_current_user(credentials=credentials, db=object())

    assert result.user is user
    assert result.roles == ["manager"]


@pytest.mark.asyncio
async def test_require_admin_user_checks_roles():
    with pytest.raises(HTTPException) as exc_info:
        await require_admin_user(make_actor(1, ["user"]))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"

    admin = make_actor(2, ["admin"])
    assert await require_admin_user(admin) is admin


@pytest.mark.asyncio
async def test_require_permission_dependency_returns_current_user(monkeypatch):
    actor = make_actor(5, ["user"])
    repository = SimpleNamespace(has_permission=AsyncMock(return_value=True))
    monkeypatch.setattr("src.utils.permissions.AccessControlRepository", lambda _db: repository)
    dependency = require_permission("mock:projects:list", "read")

    result = await dependency(current_user=actor, db=object())

    assert result is actor
    repository.has_permission.assert_awaited_once_with(
        user_id=5,
        resource_code="mock:projects:list",
        permission_code="read",
    )


@pytest.mark.asyncio
async def test_require_permission_dependency_raises_when_forbidden(monkeypatch):
    actor = make_actor(6, ["user"])
    repository = SimpleNamespace(has_permission=AsyncMock(return_value=False))
    monkeypatch.setattr("src.utils.permissions.AccessControlRepository", lambda _db: repository)
    dependency = require_permission("mock:documents:list", "read")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user=actor, db=object())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"
