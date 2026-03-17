from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User
from src.repositories.users import UserRepository
from src.utils.config import settings
from src.utils.db import get_db


security = HTTPBearer(auto_error=False)


@dataclass
class RequestUser:
    """Аутентифицированный пользователь запроса с уже загруженными ролями."""

    user: User
    roles: list[str]

    @property
    def id(self) -> int:
        """Возвращает идентификатор пользователя."""

        return self.user.id

    def has_role(self, role_name: str) -> bool:
        """Проверяет наличие роли у текущего пользователя."""

        return role_name in self.roles


def create_access_token(user_id: int, roles: list[str]) -> str:
    """Создает JWT access token для пользователя."""

    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def generate_refresh_token() -> str:
    """Генерирует криптографически стойкий refresh token."""

    return secrets.token_urlsafe(32)


def get_refresh_token_expires_at() -> datetime:
    """Возвращает дату истечения refresh token."""

    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)


def decode_access_token(token: str) -> dict:
    """Декодирует JWT access token и возвращает payload."""

    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> RequestUser:
    """
    Возвращает текущего аутентифицированного пользователя по Bearer token.

    Raises:
        HTTPException: 401 если токен отсутствует, невалиден или пользователь недоступен.
    """

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from None

    repository = UserRepository(db)
    user = await repository.get_by_id(user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not available",
        )

    roles = await repository.get_role_names(user.id)
    return RequestUser(user=user, roles=roles)


async def require_admin_user(
    current_user: RequestUser = Depends(get_current_user),
) -> RequestUser:
    """
    Ограничивает доступ только пользователями с ролью `admin` или `superadmin`.

    Raises:
        HTTPException: 403 если у пользователя нет административной роли.
    """

    if not (current_user.has_role("admin") or current_user.has_role("superadmin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return current_user

