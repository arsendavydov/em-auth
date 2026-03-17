from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.schemas.auth import LoginRequest, RefreshTokenRequest
from src.services.auth import AuthService


def make_repository():
    repository = SimpleNamespace()
    repository.session = object()
    repository.get_by_email = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_role_names = AsyncMock()
    repository.commit = AsyncMock()
    return repository


@pytest.mark.asyncio
async def test_login_returns_tokens(monkeypatch):
    repository = make_repository()
    repository.get_by_email.return_value = SimpleNamespace(
        id=1,
        email="admin@em.ru",
        password_hash="hashed",
        is_active=True,
        deleted_at=None,
    )
    repository.get_role_names.return_value = ["admin"]

    service = AuthService(repository)
    service.refresh_token_repository = SimpleNamespace(
        create_token=AsyncMock(),
        get_by_token=AsyncMock(),
        revoke_token=AsyncMock(),
        revoke_all_user_tokens=AsyncMock(),
    )

    monkeypatch.setattr("src.services.auth.verify_password", lambda *_: True)
    monkeypatch.setattr("src.services.auth.create_access_token", lambda **_: "access")
    monkeypatch.setattr("src.services.auth.generate_refresh_token", lambda: "refresh")
    monkeypatch.setattr("src.services.auth.get_refresh_token_expires_at", lambda: "expires")

    result = await service.login(
        LoginRequest(email="admin@em.ru", password="password123")
    )

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"
    service.refresh_token_repository.create_token.assert_awaited_once_with(
        1, "refresh", "expires"
    )
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_raises_for_missing_user():
    repository = make_repository()
    repository.get_by_email.return_value = None
    service = AuthService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.login(LoginRequest(email="admin@em.ru", password="password123"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_raises_for_invalid_password(monkeypatch):
    repository = make_repository()
    repository.get_by_email.return_value = SimpleNamespace(
        id=1,
        email="admin@em.ru",
        password_hash="hashed",
        is_active=True,
        deleted_at=None,
    )
    service = AuthService(repository)

    monkeypatch.setattr("src.services.auth.verify_password", lambda *_: False)

    with pytest.raises(HTTPException) as exc_info:
        await service.login(LoginRequest(email="admin@em.ru", password="password123"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password"


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(monkeypatch):
    repository = make_repository()
    repository.get_by_id.return_value = SimpleNamespace(
        id=5,
        email="user@em.ru",
        is_active=True,
        deleted_at=None,
    )
    repository.get_role_names.return_value = ["user"]

    service = AuthService(repository)
    service.refresh_token_repository = SimpleNamespace(
        create_token=AsyncMock(),
        get_by_token=AsyncMock(return_value=SimpleNamespace(user_id=5)),
        revoke_token=AsyncMock(),
        revoke_all_user_tokens=AsyncMock(),
    )

    monkeypatch.setattr("src.services.auth.create_access_token", lambda **_: "new-access")
    monkeypatch.setattr("src.services.auth.generate_refresh_token", lambda: "new-refresh")
    monkeypatch.setattr("src.services.auth.get_refresh_token_expires_at", lambda: "expires")

    result = await service.refresh(RefreshTokenRequest(refresh_token="old-refresh"))

    assert result.access_token == "new-access"
    assert result.refresh_token == "new-refresh"
    service.refresh_token_repository.revoke_token.assert_awaited_once_with("old-refresh")
    service.refresh_token_repository.create_token.assert_awaited_once_with(
        5, "new-refresh", "expires"
    )
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_raises_for_invalid_token():
    repository = make_repository()
    service = AuthService(repository)
    service.refresh_token_repository = SimpleNamespace(
        create_token=AsyncMock(),
        get_by_token=AsyncMock(return_value=None),
        revoke_token=AsyncMock(),
        revoke_all_user_tokens=AsyncMock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(RefreshTokenRequest(refresh_token="bad"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_refresh_raises_for_unavailable_user():
    repository = make_repository()
    repository.get_by_id.return_value = SimpleNamespace(
        id=5,
        email="user@em.ru",
        is_active=False,
        deleted_at=None,
    )
    service = AuthService(repository)
    service.refresh_token_repository = SimpleNamespace(
        create_token=AsyncMock(),
        get_by_token=AsyncMock(return_value=SimpleNamespace(user_id=5)),
        revoke_token=AsyncMock(),
        revoke_all_user_tokens=AsyncMock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(RefreshTokenRequest(refresh_token="old-refresh"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User is not available"


@pytest.mark.asyncio
async def test_logout_revokes_all_user_tokens():
    repository = make_repository()
    service = AuthService(repository)
    service.refresh_token_repository = SimpleNamespace(
        create_token=AsyncMock(),
        get_by_token=AsyncMock(),
        revoke_token=AsyncMock(),
        revoke_all_user_tokens=AsyncMock(),
    )

    await service.logout(11)

    service.refresh_token_repository.revoke_all_user_tokens.assert_awaited_once_with(11)
    repository.commit.assert_awaited_once()
