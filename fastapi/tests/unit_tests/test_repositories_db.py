from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.access_admin import AccessAdminRepository
from src.repositories.access_control import AccessControlRepository
from src.repositories.mappers.base import DataMapper
from src.repositories.refresh_tokens import RefreshTokenRepository
from src.repositories.users import UserRepository
from src.utils import db as db_module
from src.utils.startup import shutdown_handler, startup_handler


class FakeExecuteResult:
    def __init__(self, scalar_one=None, scalars_all=None, rows=None):
        self._scalar_one = scalar_one
        self._scalars_all = scalars_all if scalars_all is not None else []
        self._rows = rows if rows is not None else []

    def scalar_one_or_none(self):
        return self._scalar_one

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars_all)

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_access_admin_repository_methods():
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                FakeExecuteResult(scalars_all=[SimpleNamespace(id=1)]),
                FakeExecuteResult(scalars_all=[SimpleNamespace(id=2)]),
                FakeExecuteResult(scalars_all=[SimpleNamespace(id=3)]),
                FakeExecuteResult(rows=[("rule", "admin", "code", "read")]),
                FakeExecuteResult(scalar_one="rule-1"),
                FakeExecuteResult(scalar_one=1),
                FakeExecuteResult(scalar_one=2),
                FakeExecuteResult(scalar_one=3),
                FakeExecuteResult(scalar_one="existing-rule"),
            ]
        ),
        add=MagicMock(),
        flush=AsyncMock(),
        refresh=AsyncMock(),
        delete=AsyncMock(),
        commit=AsyncMock(),
    )
    repository = AccessAdminRepository(session)
    rule = SimpleNamespace(id=10)

    assert await repository.list_roles() == [SimpleNamespace(id=1)]
    assert await repository.list_resources() == [SimpleNamespace(id=2)]
    assert await repository.list_permissions() == [SimpleNamespace(id=3)]
    assert await repository.list_rules() == [("rule", "admin", "code", "read")]
    assert await repository.get_rule(1) == "rule-1"
    assert await repository.role_exists(1) is True
    assert await repository.resource_exists(2) is True
    assert await repository.permission_exists(3) is True
    assert await repository.find_rule(1, 2, 3) == "existing-rule"

    returned = await repository.add_rule(rule)
    assert returned is rule
    session.add.assert_called_once_with(rule)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(rule)

    await repository.delete_rule(rule)
    session.delete.assert_awaited_once_with(rule)

    await repository.commit()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_token_repository_methods():
    revocable_token = SimpleNamespace(is_revoked=False)
    token_a = SimpleNamespace(is_revoked=False)
    token_b = SimpleNamespace(is_revoked=False)
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                FakeExecuteResult(scalar_one="stored-token"),
                FakeExecuteResult(scalar_one=revocable_token),
                FakeExecuteResult(scalar_one=None),
                FakeExecuteResult(scalars_all=[token_a, token_b]),
            ]
        ),
        add=MagicMock(),
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )
    repository = RefreshTokenRepository(session)
    expires_at = datetime.now(UTC)

    created = await repository.create_token(1, "token", expires_at)
    assert created.user_id == 1
    assert created.token == "token"
    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()

    assert await repository.get_by_token("token") == "stored-token"

    await repository.revoke_token("token")
    await repository.revoke_token("missing")
    await repository.revoke_all_user_tokens(1)

    assert revocable_token.is_revoked is True
    assert token_a.is_revoked is True
    assert token_b.is_revoked is True
    assert session.flush.await_count == 3


@pytest.mark.asyncio
async def test_user_repository_methods():
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                FakeExecuteResult(scalar_one="user-by-email"),
                FakeExecuteResult(scalar_one="user-by-id"),
                FakeExecuteResult(scalars_all=["active-1", "active-2"]),
                FakeExecuteResult(scalars_all=["admin", "user"]),
            ]
        ),
        add=MagicMock(),
        flush=AsyncMock(),
        refresh=AsyncMock(),
        commit=AsyncMock(),
    )
    repository = UserRepository(session)
    user = SimpleNamespace(id=1)

    assert await repository.get_by_email("mail@em.ru") == "user-by-email"
    assert await repository.get_by_id(1) == "user-by-id"
    assert await repository.list_active_users() == ["active-1", "active-2"]
    assert await repository.get_role_names(1) == ["admin", "user"]

    returned = await repository.add(user)
    assert returned is user
    session.add.assert_called_once_with(user)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(user)

    await repository.refresh(user)
    assert session.refresh.await_count == 2

    await repository.commit()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_access_control_repository_checks_permission():
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                FakeExecuteResult(scalar_one=1),
                FakeExecuteResult(scalar_one=None),
            ]
        )
    )
    repository = AccessControlRepository(session)

    assert await repository.has_permission(1, "mock:projects:list", "read") is True
    assert await repository.has_permission(1, "mock:documents:list", "read") is False


def test_data_mapper_base_methods_raise():
    with pytest.raises(NotImplementedError):
        DataMapper.to_schema(object())

    with pytest.raises(NotImplementedError):
        DataMapper.from_schema(object())


@pytest.mark.asyncio
async def test_db_helpers_and_startup_shutdown(monkeypatch):
    session = object()

    class FakeSessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    begin_connection = SimpleNamespace(execute=AsyncMock())

    class FakeBeginContext:
        async def __aenter__(self):
            return begin_connection

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(db_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(db_module, "engine", SimpleNamespace(begin=FakeBeginContext, dispose=AsyncMock()))

    generator = db_module.get_db()
    yielded = await anext(generator)
    assert yielded is session
    with pytest.raises(StopAsyncIteration):
        await anext(generator)

    await db_module.check_connection()
    begin_connection.execute.assert_awaited_once()

    await db_module.close_engine()
    db_module.engine.dispose.assert_awaited_once()

    check_connection_mock = AsyncMock()
    close_engine_mock = AsyncMock()
    monkeypatch.setattr("src.utils.startup.check_connection", check_connection_mock)
    monkeypatch.setattr("src.utils.startup.close_engine", close_engine_mock)

    await startup_handler()
    await shutdown_handler()

    check_connection_mock.assert_awaited_once()
    close_engine_mock.assert_awaited_once()
