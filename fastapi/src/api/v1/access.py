from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.access_admin import AccessAdminRepository
from src.schemas.access import (
    AccessRuleCreate,
    AccessRuleRead,
    AccessRuleUpdate,
    PermissionRead,
    ResourceRead,
    RoleRead,
)
from src.schemas.common import MessageResponse
from src.services.access import AccessAdminService
from src.utils.auth import RequestUser, require_admin_user
from src.utils.db import get_db

router = APIRouter(prefix="/access", tags=["access"])

ACCESS_401_RESPONSE = {
    "description": "Пользователь не аутентифицирован или access token невалиден.",
}
ACCESS_403_RESPONSE = {
    "description": "Доступ разрешен только пользователям с ролью admin или superadmin.",
}
ACCESS_404_RESPONSE = {
    "description": "Роль, ресурс, действие или правило доступа не найдены.",
}


def get_access_service(db: AsyncSession = Depends(get_db)) -> AccessAdminService:
    """Создает сервис администрирования правил доступа для текущего запроса."""

    repository = AccessAdminRepository(db)
    return AccessAdminService(repository)


@router.get(
    "/roles",
    response_model=list[RoleRead],
    summary="Получить список ролей",
    description="Возвращает список всех ролей, доступных в системе управления доступом.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
    },
)
async def list_roles(
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> list[RoleRead]:
    """Возвращает список ролей для администратора."""

    return await service.list_roles()


@router.get(
    "/resources",
    response_model=list[ResourceRead],
    summary="Получить список ресурсов",
    description="Возвращает список ресурсов, к которым могут применяться правила доступа.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
    },
)
async def list_resources(
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> list[ResourceRead]:
    """Возвращает список ресурсов для администратора."""

    return await service.list_resources()


@router.get(
    "/permissions",
    response_model=list[PermissionRead],
    summary="Получить список действий",
    description="Возвращает список действий (`permissions`), используемых в правилах доступа.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
    },
)
async def list_permissions(
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> list[PermissionRead]:
    """Возвращает список действий для администратора."""

    return await service.list_permissions()


@router.get(
    "/rules",
    response_model=list[AccessRuleRead],
    summary="Получить список правил доступа",
    description="Возвращает все текущие правила доступа с расшифровкой роли, ресурса и действия.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
    },
)
async def list_rules(
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> list[AccessRuleRead]:
    """Возвращает список правил доступа для администратора."""

    return await service.list_rules()


@router.post(
    "/rules",
    response_model=AccessRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать правило доступа",
    description=(
        "Создает новое правило доступа для выбранной роли, ресурса и действия. Повторяющееся правило создать нельзя."
    ),
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
        404: ACCESS_404_RESPONSE,
        409: {"description": "Правило доступа с такой комбинацией уже существует."},
    },
)
async def create_rule(
    payload: AccessRuleCreate,
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> AccessRuleRead:
    """Создает новое правило доступа."""

    return await service.create_rule(payload)


@router.patch(
    "/rules/{rule_id}",
    response_model=AccessRuleRead,
    summary="Изменить правило доступа",
    description="Изменяет флаг разрешения у существующего правила доступа.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
        404: ACCESS_404_RESPONSE,
    },
)
async def update_rule(
    rule_id: int,
    payload: AccessRuleUpdate,
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> AccessRuleRead:
    """Обновляет существующее правило доступа."""

    return await service.update_rule(rule_id, payload)


@router.delete(
    "/rules/{rule_id}",
    response_model=MessageResponse,
    summary="Удалить правило доступа",
    description="Удаляет правило доступа по его идентификатору.",
    responses={
        401: ACCESS_401_RESPONSE,
        403: ACCESS_403_RESPONSE,
        404: ACCESS_404_RESPONSE,
    },
)
async def delete_rule(
    rule_id: int,
    current_user: RequestUser = Depends(require_admin_user),
    service: AccessAdminService = Depends(get_access_service),
) -> MessageResponse:
    """Удаляет правило доступа."""

    await service.delete_rule(rule_id)
    return MessageResponse()
