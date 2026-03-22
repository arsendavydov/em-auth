"""
Зависимости авторизации к ресурсам по модели RBAC (таблицы access_rules).

Это не то же самое, что матрица «кто может редактировать пользователя» в UserService:
там системные роли (admin/superadmin/…); здесь — произвольные ресурсы и действия из БД.
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.access_control import AccessControlRepository
from src.utils.auth import RequestUser, get_current_user
from src.utils.db import get_db


def require_permission(
    resource_code: str,
    permission_code: str,
) -> Callable[..., object]:
    """
    Создает dependency для проверки права на конкретный ресурс и действие.

    Args:
        resource_code: Код ресурса в системе доступа.
        permission_code: Код действия в системе доступа.

    Returns:
        Зависимость FastAPI, проверяющую право доступа.
    """

    async def dependency(
        current_user: RequestUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> RequestUser:
        """Проверяет доступ текущего пользователя к ресурсу и действию."""

        # Запрос в БД: есть ли у любой роли пользователя разрешающее правило.
        access_repository = AccessControlRepository(db)

        has_access = await access_repository.has_permission(
            user_id=current_user.id,
            resource_code=resource_code,
            permission_code=permission_code,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return current_user

    return dependency
