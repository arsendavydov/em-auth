import os
import time
import uuid
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from src.models.access_rules import AccessRule
from src.models.permissions import Permission
from src.models.resources import Resource
from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.users import User

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=False)

TEST_BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

REQUIRED_ENV_VARS = {
    "TEST_DATABASE_URL": TEST_DATABASE_URL,
    "TEST_PASSWORD": TEST_PASSWORD,
}

missing_env = [name for name, value in REQUIRED_ENV_VARS.items() if not value]
if missing_env:
    raise ValueError(
        "Missing required test env vars in .env: " + ", ".join(sorted(missing_env))
    )


def unique_email(prefix: str = "e2e") -> str:
    suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    return f"{prefix}_{suffix}@em.ru"


class ApiHelper:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def register_user(
        self,
        email: str,
        password: str = TEST_PASSWORD,
        first_name: str = "Test",
        last_name: str = "User",
        middle_name: str | None = None,
    ) -> httpx.Response:
        payload = {
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
        }
        return self.client.post("/api/v1/users/register", json=payload)

    def login(self, email: str, password: str = TEST_PASSWORD) -> httpx.Response:
        return self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

    def auth_headers(self, email: str, password: str = TEST_PASSWORD) -> dict[str, str]:
        response = self.login(email=email, password=password)
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def get_me(self, headers: dict[str, str]) -> httpx.Response:
        return self.client.get("/api/v1/users/me", headers=headers)

    def best_effort_delete_user(self, email: str, password: str = TEST_PASSWORD) -> None:
        login_response = self.login(email=email, password=password)
        if login_response.status_code != 200:
            return
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        self.client.delete("/api/v1/users/me", headers=headers)


class E2EDbHelper:
    def __init__(self, database_url: str) -> None:
        sync_database_url = database_url.replace("+asyncpg", "+psycopg2")
        self._engine = create_engine(sync_database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=Session,
            expire_on_commit=False,
        )

    def assign_role(self, email: str, role_name: str) -> None:
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.email == email))
            if user is None:
                raise AssertionError(f"User not found for role assignment: {email}")

            role = session.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                raise AssertionError(f"Role not found: {role_name}")

            existing_link = session.scalar(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                )
            )
            if existing_link is None:
                session.add(UserRole(user_id=user.id, role_id=role.id))
                session.commit()

    def hard_delete_user(self, email: str) -> None:
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.email == email))
            if user is None:
                return

            session.execute(delete(UserRole).where(UserRole.user_id == user.id))
            session.delete(user)
            session.commit()

    def delete_access_rule(
        self,
        role_name: str,
        resource_code: str,
        permission_code: str,
    ) -> None:
        with self._session_factory() as session:
            role = session.scalar(select(Role).where(Role.name == role_name))
            resource = session.scalar(select(Resource).where(Resource.code == resource_code))
            permission = session.scalar(select(Permission).where(Permission.code == permission_code))

            if role is None or resource is None or permission is None:
                return

            session.execute(
                delete(AccessRule).where(
                    AccessRule.role_id == role.id,
                    AccessRule.resource_id == resource.id,
                    AccessRule.permission_id == permission.id,
                )
            )
            session.commit()


@pytest.fixture(scope="session")
def base_url() -> str:
    return TEST_BASE_URL


@pytest.fixture(scope="session")
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=20.0, follow_redirects=True) as http_client:
        yield http_client


@pytest.fixture(scope="session")
def api(client: httpx.Client) -> ApiHelper:
    return ApiHelper(client)


@pytest.fixture(scope="session")
def e2e_db() -> E2EDbHelper:
    helper = E2EDbHelper(database_url=TEST_DATABASE_URL)
    yield helper
    helper._engine.dispose()


@pytest.fixture(scope="function")
def fresh_email() -> str:
    return unique_email()


@pytest.fixture(scope="function")
def account_factory(api: ApiHelper, e2e_db: E2EDbHelper):
    created_emails: list[str] = []

    def _create(
        role_name: str | None = None,
        prefix: str = "e2e_user",
        first_name: str = "Test",
        last_name: str = "User",
        middle_name: str | None = None,
    ) -> dict[str, object]:
        email = unique_email(prefix)
        response = api.register_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        assert response.status_code == 201, response.text
        if role_name is not None:
            e2e_db.assign_role(email=email, role_name=role_name)
        created_emails.append(email)
        return {
            "email": email,
            "response": response,
            "user": response.json(),
        }

    try:
        yield _create
    finally:
        for email in reversed(created_emails):
            e2e_db.hard_delete_user(email)


@pytest.fixture(scope="function")
def created_accounts(account_factory) -> dict[str, str]:
    return {
        "admin1": account_factory(role_name="admin", prefix="e2e_admin1")["email"],
        "admin2": account_factory(role_name="admin", prefix="e2e_admin2")["email"],
        "manager1": account_factory(role_name="manager", prefix="e2e_manager1")["email"],
        "manager2": account_factory(role_name="manager", prefix="e2e_manager2")["email"],
        "user1": account_factory(role_name="user", prefix="e2e_user1")["email"],
        "user2": account_factory(role_name="user", prefix="e2e_user2")["email"],
    }


@pytest.fixture(scope="session")
def shared_test_password() -> str:
    return TEST_PASSWORD
