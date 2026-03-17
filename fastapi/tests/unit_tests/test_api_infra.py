import importlib
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request, Response
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError
from starlette.requests import Request as StarletteRequest

from src.api.v1 import access as access_api
from src.api.v1 import auth as auth_api
from src.api.v1 import health as health_api
from src.api.v1 import mock as mock_api
from src.api.v1 import users as users_api
from src.exceptions.base import DomainException
from src.middleware.exception_handler import (
    database_exception_handler,
    domain_exception_handler,
    general_exception_handler,
)
from src.middleware.http_logging import HTTPLoggingMiddleware
from src.schemas.access import AccessRuleCreate, AccessRuleUpdate
from src.schemas.auth import LoginRequest, RefreshTokenRequest
from src.schemas.users import UserCreate, UserUpdate
from src.utils.auth import RequestUser
from src.utils.logger import JsonFormatter, _create_handlers, _use_json_logs, get_logger, setup_logging


def make_actor() -> RequestUser:
    return RequestUser(user=SimpleNamespace(id=1, is_active=True, deleted_at=None), roles=["admin"])


def make_request() -> Request:
    return StarletteRequest(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "query_string": b"",
            "http_version": "1.1",
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


def make_request_with_query() -> Request:
    return StarletteRequest(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "query_string": b"page=1",
            "http_version": "1.1",
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


def test_logger_helpers(monkeypatch, tmp_path):
    root_logger = logging.getLogger()
    original_root_handlers = list(root_logger.handlers)
    original_root_level = root_logger.level
    tracked_logger_names = ["uvicorn", "uvicorn.error", "fastapi", "alembic", "sqlalchemy.engine"]
    original_logger_states = {
        name: (
            list(logging.getLogger(name).handlers),
            logging.getLogger(name).level,
            logging.getLogger(name).propagate,
        )
        for name in tracked_logger_names
    }

    monkeypatch.setenv("LOG_FORMAT_JSON", "true")
    assert _use_json_logs() is True

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    payload = json.loads(formatter.format(record))
    assert payload["message"] == "hello"

    file_handler, console_handler = _create_handlers(tmp_path / "app.log", logging.INFO)
    assert file_handler.level == logging.INFO
    assert console_handler.level == logging.INFO

    file_stub = MagicMock()
    file_stub.level = logging.INFO
    console_stub = MagicMock()
    console_stub.level = logging.INFO
    monkeypatch.setattr("src.utils.logger._create_handlers", lambda *_args, **_kwargs: (file_stub, console_stub))

    try:
        setup_logging("test.log")

        root_logger = logging.getLogger()
        assert file_stub in root_logger.handlers
        assert console_stub in root_logger.handlers
        assert get_logger("custom.name").name == "custom.name"
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_root_handlers)
        root_logger.setLevel(original_root_level)

        for name, (handlers, level, propagate) in original_logger_states.items():
            logger = logging.getLogger(name)
            logger.handlers.clear()
            logger.handlers.extend(handlers)
            logger.setLevel(level)
            logger.propagate = propagate


@pytest.mark.asyncio
async def test_exception_handlers_return_expected_responses(monkeypatch):
    logger_mock = MagicMock()
    monkeypatch.setattr("src.middleware.exception_handler.logger", logger_mock)
    request = make_request()

    integrity_response = await database_exception_handler(
        request,
        IntegrityError("stmt", {}, Exception("boom")),
    )
    operational_response = await database_exception_handler(
        request,
        OperationalError("stmt", {}, Exception("boom")),
    )
    generic_response = await database_exception_handler(
        request,
        DatabaseError("stmt", {}, Exception("boom")),
    )
    domain_response = await domain_exception_handler(
        request,
        DomainException("domain boom", status_code=422),
    )
    general_response = await general_exception_handler(request, RuntimeError("boom"))

    assert integrity_response.status_code == 409
    assert operational_response.status_code == 503
    assert generic_response.status_code == 500
    assert domain_response.status_code == 422
    assert general_response.status_code == 500
    assert logger_mock.error.call_count == 5


@pytest.mark.asyncio
async def test_http_logging_middleware_logs_success_and_exception(caplog):
    app = FastAPI()
    middleware = HTTPLoggingMiddleware(app)
    request = make_request_with_query()

    with caplog.at_level(logging.INFO):
        response = await middleware.dispatch(
            request,
            AsyncMock(return_value=Response(status_code=201)),
        )
    assert response.status_code == 201

    with caplog.at_level(logging.INFO):
        with pytest.raises(RuntimeError):
            await middleware.dispatch(
                request,
                AsyncMock(side_effect=RuntimeError("boom")),
            )

    assert any('GET /test?page=1 HTTP/1.1" 201' in message for message in caplog.messages)
    assert any('GET /test?page=1 HTTP/1.1" 500' in message for message in caplog.messages)


@pytest.mark.asyncio
async def test_health_routes_and_mock_routes():
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar=lambda: 1)))
    ready = await health_api.ready(db)
    not_ready = await health_api.ready(SimpleNamespace(execute=AsyncMock(side_effect=RuntimeError("db down"))))
    health = await health_api.health()

    projects = await mock_api.list_mock_projects(make_actor())
    reports = await mock_api.list_mock_reports(make_actor())
    documents = await mock_api.list_mock_documents(make_actor())

    assert health["status"] == "ok"
    assert ready["ready"] is True
    assert not_ready["ready"] is False
    assert "error" in not_ready
    assert len(projects) == 2
    assert len(reports) == 2
    assert len(documents) == 2


@pytest.mark.asyncio
async def test_auth_routes_and_service_factory():
    db = object()
    service = auth_api.get_auth_service(db=db)
    actor = make_actor()
    fake_service = SimpleNamespace(
        login=AsyncMock(return_value="login-ok"),
        refresh=AsyncMock(return_value="refresh-ok"),
        logout=AsyncMock(),
    )

    login_result = await auth_api.login(
        LoginRequest(email="user@em.ru", password="secret123"),
        service=fake_service,
    )
    refresh_result = await auth_api.refresh(
        RefreshTokenRequest(refresh_token="token"),
        service=fake_service,
    )
    logout_result = await auth_api.logout(actor, service=fake_service)

    assert service.repository.session is db
    assert login_result == "login-ok"
    assert refresh_result == "refresh-ok"
    assert logout_result.status == "OK"
    fake_service.logout.assert_awaited_once_with(actor.id)


@pytest.mark.asyncio
async def test_user_routes_and_service_factory():
    db = object()
    service = users_api.get_user_service(db=db)
    actor = make_actor()
    fake_service = SimpleNamespace(
        register_user=AsyncMock(return_value="registered"),
        get_me=AsyncMock(return_value="me"),
        list_users=AsyncMock(return_value=["u1"]),
        get_user=AsyncMock(return_value="user"),
        update_user=AsyncMock(return_value="updated"),
        soft_delete_user=AsyncMock(),
    )
    create_payload = UserCreate(
        email="new@em.ru",
        password="secret123",
        password_confirm="secret123",
        first_name="New",
        last_name="User",
    )
    update_payload = UserUpdate(first_name="Updated")

    assert service.repository.session is db
    assert await users_api.register_user(create_payload, service=fake_service) == "registered"
    assert await users_api.get_me(actor, service=fake_service) == "me"
    assert await users_api.list_users(actor, service=fake_service) == ["u1"]
    assert await users_api.get_user(2, actor, service=fake_service) == "user"
    assert await users_api.update_me(update_payload, actor, service=fake_service) == "updated"
    assert await users_api.update_user(2, update_payload, actor, service=fake_service) == "updated"

    delete_me_response = await users_api.delete_me(actor, service=fake_service)
    delete_user_response = await users_api.delete_user(2, actor, service=fake_service)

    assert delete_me_response.status == "OK"
    assert delete_user_response.status == "OK"
    fake_service.soft_delete_user.assert_any_await(actor, actor.id)
    fake_service.soft_delete_user.assert_any_await(actor, 2)


@pytest.mark.asyncio
async def test_access_routes_and_service_factory():
    db = object()
    service = access_api.get_access_service(db=db)
    actor = make_actor()
    fake_service = SimpleNamespace(
        list_roles=AsyncMock(return_value=["roles"]),
        list_resources=AsyncMock(return_value=["resources"]),
        list_permissions=AsyncMock(return_value=["permissions"]),
        list_rules=AsyncMock(return_value=["rules"]),
        create_rule=AsyncMock(return_value="created"),
        update_rule=AsyncMock(return_value="updated"),
        delete_rule=AsyncMock(),
    )
    create_payload = AccessRuleCreate(
        role_id=1,
        resource_id=2,
        permission_id=3,
        is_allowed=True,
    )
    update_payload = AccessRuleUpdate(is_allowed=False)

    assert service.repository.session is db
    assert await access_api.list_roles(actor, service=fake_service) == ["roles"]
    assert await access_api.list_resources(actor, service=fake_service) == ["resources"]
    assert await access_api.list_permissions(actor, service=fake_service) == ["permissions"]
    assert await access_api.list_rules(actor, service=fake_service) == ["rules"]
    assert await access_api.create_rule(create_payload, actor, service=fake_service) == "created"
    assert await access_api.update_rule(7, update_payload, actor, service=fake_service) == "updated"

    delete_response = await access_api.delete_rule(7, actor, service=fake_service)
    assert delete_response.status == "OK"
    fake_service.delete_rule.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_main_create_app_and_lifespan(monkeypatch):
    import src.main as main_module

    startup_mock = AsyncMock()
    shutdown_mock = AsyncMock()
    monkeypatch.setattr(main_module, "startup_handler", startup_mock)
    monkeypatch.setattr(main_module, "shutdown_handler", shutdown_mock)

    importlib.reload(main_module)
    monkeypatch.setattr(main_module, "startup_handler", startup_mock)
    monkeypatch.setattr(main_module, "shutdown_handler", shutdown_mock)
    app = main_module.create_app()

    paths = {route.path for route in app.routes}
    assert "/api/v1/health" in paths
    assert "/api/v1/users/me" in paths
    assert "/api/v1/auth/login" in paths
    assert main_module.app is not None

    async with main_module.lifespan(app):
        pass

    startup_mock.assert_awaited()
    shutdown_mock.assert_awaited()
