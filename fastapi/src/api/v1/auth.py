"""
HTTP-ручки входа, обновления пары токенов и выхода.

Тело ответов об ошибках — на английском (единый контракт); бизнес-логика в AuthService.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.users import UserRepository
from src.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from src.schemas.common import MessageResponse
from src.services.auth import AuthService
from src.utils.auth import RequestUser, get_current_user
from src.utils.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_401_RESPONSE = {
    "description": "Пользователь не аутентифицирован, токен невалиден или учетная запись недоступна.",
}


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Создает сервис аутентификации для текущего запроса."""

    repository = UserRepository(db)
    return AuthService(repository)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Войти в систему",
    description=(
        "Аутентифицирует пользователя по email и паролю. При успехе возвращает JWT доступа и токен обновления сессии (refresh)."
    ),
    responses={
        401: AUTH_401_RESPONSE,
    },
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Выполняет вход пользователя в систему.

    Args:
        payload: Данные для аутентификации пользователя.
        service: Сервис аутентификации.

    Returns:
        Пара токенов: JWT доступа и обновления сессии (refresh).

    Raises:
        HTTPException: 401 если email или пароль неверны.
    """

    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить токены",
    description=(
        "Проверяет токен обновления (refresh), отзывает его и выдаёт новую пару: JWT доступа и новый refresh."
    ),
    responses={
        401: AUTH_401_RESPONSE,
    },
)
async def refresh(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Обновляет пару токенов по валидному токену обновления (refresh).

    Args:
        payload: Тело запроса с токеном обновления.
        service: Сервис аутентификации.

    Returns:
        Новая пара: JWT доступа и токен обновления.

    Raises:
        HTTPException: 401 если токен обновления невалиден или истёк.
    """

    return await service.refresh(payload)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Выйти из системы",
    description=("Отзывает все токены обновления сессии (refresh) текущего пользователя и завершает активную сессию."),
    responses={
        401: AUTH_401_RESPONSE,
    },
)
async def logout(
    current_user: RequestUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Выполняет выход текущего пользователя из системы.

    Args:
        current_user: Текущий аутентифицированный пользователь.
        service: Сервис аутентификации.

    Returns:
        Служебный ответ со статусом выполнения операции.
    """

    await service.logout(current_user.id)
    return MessageResponse()
