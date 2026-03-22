"""
Аутентификация запросов по Bearer JWT и вспомогательные сущности.

Поток: заголовок Authorization → декод JWT (только sub + проверка подписи/exp) → загрузка User из БД
→ роли для RequestUser всегда из БД, не из payload JWT (см. get_current_user).

Функции create_access_token / decode_access_token — синхронные: PyJWT без I/O; async только get_current_user (БД).
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

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
    """Создаёт JWT токен доступа для пользователя."""

    expire_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    # В payload кладём roles для прозрачности/отладки; при запросе get_current_user роли
    # перечитываются из БД — источник правды по системным ролям там.
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def generate_refresh_token() -> str:
    """Генерирует криптографически стойкий токен обновления сессии (refresh)."""

    return secrets.token_urlsafe(32)


def get_refresh_token_expires_at() -> datetime:
    """Возвращает момент истечения срока токена обновления."""

    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)


def decode_access_token(token: str) -> dict:
    """Декодирует JWT токен доступа и возвращает payload."""

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
        # Используем только sub; роли из JWT не доверяем — см. create_access_token.
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

    # Актуальные системные роли только из БД (user_roles + roles).
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
