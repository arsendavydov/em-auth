"""
Запросы к users и связям user_roles; используется сервисами и get_current_user (роли).

populate_existing в get_by_* — подтягивать свежие данные при повторных запросах в той же сессии.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.users import User


class UserRepository:
    """Репозиторий для работы с пользователями и их ролями."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email или `None`, если запись не найдена."""

        # populate_existing: если объект User уже в сессии, обновить из результата SELECT.
        stmt = select(User).where(User.email == email).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по идентификатору или `None`, если запись не найдена."""

        # См. get_by_email — тот же смысл populate_existing.
        stmt = select(User).where(User.id == user_id).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_users(self) -> list[User]:
        """Возвращает список пользователей без мягкого удаления."""

        stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_role_names(self, user_id: int) -> list[str]:
        """Возвращает список имен ролей пользователя."""

        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_role_by_name(self, role_name: str) -> Role | None:
        """Возвращает роль по имени или `None`, если запись не найдена."""

        stmt = select(Role).where(Role.name == role_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_user_role(self, user_id: int, role_id: int) -> None:
        """Назначает пользователю роль, если такой связи еще нет."""

        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            self.session.add(UserRole(user_id=user_id, role_id=role_id))

    async def remove_user_role(self, user_id: int, role_id: int) -> bool:
        """
        Удаляет роль пользователя.

        Returns:
            True, если связь была удалена, иначе False.
        """

        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            return False

        await self.session.delete(existing)
        return True

    async def add(self, user: User) -> User:
        """Добавляет пользователя в сессию и возвращает обновленный ORM-объект."""

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def refresh(self, user: User) -> None:
        """Обновляет состояние ORM-объекта пользователя из базы данных."""

        await self.session.refresh(user)

    async def commit(self) -> None:
        """Фиксирует текущую транзакцию."""

        await self.session.commit()
