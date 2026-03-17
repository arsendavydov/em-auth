from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.common import MessageResponse
from src.schemas.users import UserCreate, UserRead, UserUpdate
from src.services.users import UserService
from src.utils.auth import RequestUser, get_current_user, require_admin_user
from src.utils.db import get_db
from src.repositories.users import UserRepository

router = APIRouter(prefix="/users", tags=["users"])

USERS_400_RESPONSE = {
    "description": "Некорректные данные запроса: email уже занят или нарушена бизнес-валидация.",
}
USERS_401_RESPONSE = {
    "description": "Пользователь не аутентифицирован или access token невалиден.",
}
USERS_403_RESPONSE = {
    "description": "Текущая роль не имеет права выполнять эту операцию.",
}
USERS_404_RESPONSE = {
    "description": "Запрошенный пользователь не найден.",
}
USERS_ROLE_404_RESPONSE = {
    "description": "Указанная роль или пользователь не найдены, или у пользователя нет такой роли.",
}


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Создает сервис пользователей для текущего запроса."""

    repo = UserRepository(db)
    return UserService(repo)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать пользователя",
    description=(
        "Создает новую учетную запись пользователя. "
        "Пароль и подтверждение пароля должны совпадать."
    ),
    responses={
        400: USERS_400_RESPONSE,
    },
)
async def register_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Регистрирует нового пользователя.

    Args:
        payload: Данные для регистрации.
        service: Сервис пользователей.

    Returns:
        Созданный пользователь.

    Raises:
        HTTPException: 400 если email уже занят или пароли не совпадают.
    """

    return await service.register_user(payload)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Получить свой профиль",
    description="Возвращает профиль текущего аутентифицированного пользователя.",
    responses={
        401: USERS_401_RESPONSE,
    },
)
async def get_me(
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Возвращает профиль текущего пользователя.

    Args:
        current_user: Текущий аутентифицированный пользователь.
        service: Сервис пользователей.

    Returns:
        Данные профиля текущего пользователя.
    """

    return await service.get_me(current_user)


@router.get(
    "",
    response_model=list[UserRead],
    summary="Получить список пользователей",
    description=(
        "Возвращает список пользователей, доступных текущему пользователю "
        "с учетом его роли и правил видимости."
    ),
    responses={
        401: USERS_401_RESPONSE,
    },
)
async def list_users(
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Возвращает список пользователей, доступных текущему пользователю."""

    return await service.list_users(current_user)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Получить пользователя по идентификатору",
    description=(
        "Возвращает данные конкретного пользователя, если текущая роль "
        "имеет право на просмотр этой учетной записи."
    ),
    responses={
        401: USERS_401_RESPONSE,
        403: USERS_403_RESPONSE,
        404: USERS_404_RESPONSE,
    },
)
async def get_user(
    user_id: int,
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Возвращает пользователя по идентификатору с учетом прав доступа."""

    return await service.get_user(current_user, user_id)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновить свой профиль",
    description="Частично обновляет данные текущего аутентифицированного пользователя.",
    responses={
        400: USERS_400_RESPONSE,
        401: USERS_401_RESPONSE,
    },
)
async def update_me(
    payload: UserUpdate,
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Обновляет профиль текущего пользователя."""

    return await service.update_user(current_user, current_user.id, payload)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Обновить пользователя",
    description=(
        "Частично обновляет другого пользователя, если это разрешено "
        "ролью текущего пользователя."
    ),
    responses={
        400: USERS_400_RESPONSE,
        401: USERS_401_RESPONSE,
        403: USERS_403_RESPONSE,
        404: USERS_404_RESPONSE,
    },
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Обновляет произвольного пользователя с учетом ролевых ограничений."""

    return await service.update_user(current_user, user_id, payload)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Удалить свой аккаунт",
    description=(
        "Выполняет мягкое удаление текущего пользователя, отзывает его "
        "refresh токены и деактивирует учетную запись."
    ),
    responses={
        401: USERS_401_RESPONSE,
    },
)
async def delete_me(
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    """Мягко удаляет текущего пользователя."""

    await service.soft_delete_user(current_user, current_user.id)
    return MessageResponse()


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Удалить пользователя",
    description=(
        "Выполняет мягкое удаление указанного пользователя, если роль "
        "текущего пользователя это позволяет."
    ),
    responses={
        401: USERS_401_RESPONSE,
        403: USERS_403_RESPONSE,
        404: USERS_404_RESPONSE,
    },
)
async def delete_user(
    user_id: int,
    current_user: RequestUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    """Мягко удаляет указанного пользователя с учетом ролевых ограничений."""

    await service.soft_delete_user(current_user, user_id)
    return MessageResponse()


@router.post(
    "/{user_id}/roles/{role_name}",
    response_model=UserRead,
    summary="Назначить роль пользователю",
    description=(
        "Назначает указанную роль пользователю. Доступно только для пользователей с ролями "
        "`admin` или `superadmin`. Управление ролью `superadmin` разрешено только `superadmin`."
    ),
    responses={
        401: USERS_401_RESPONSE,
        403: USERS_403_RESPONSE,
        404: USERS_ROLE_404_RESPONSE,
    },
)
async def assign_role_to_user(
    user_id: int,
    role_name: str,
    current_user: RequestUser = Depends(require_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Назначает пользователю роль с учетом ролевых ограничений."""

    return await service.assign_role(current_user, user_id, role_name)


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=UserRead,
    summary="Удалить роль у пользователя",
    description=(
        "Удаляет указанную роль у пользователя. Доступно только для пользователей с ролями "
        "`admin` или `superadmin`. Управление ролью `superadmin` разрешено только `superadmin`."
    ),
    responses={
        401: USERS_401_RESPONSE,
        403: USERS_403_RESPONSE,
        404: USERS_ROLE_404_RESPONSE,
    },
)
async def remove_role_from_user(
    user_id: int,
    role_name: str,
    current_user: RequestUser = Depends(require_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Удаляет роль пользователя с учетом ролевых ограничений."""

    return await service.remove_role(current_user, user_id, role_name)

