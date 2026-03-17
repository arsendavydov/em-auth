from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.users import User


class UserRepository:
    """Репозиторий для работы с пользователями и их ролями."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        """Возвращает пользователя по email или `None`, если запись не найдена."""

        stmt = (
            select(User)
            .where(User.email == email)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Возвращает пользователя по идентификатору или `None`, если запись не найдена."""

        stmt = (
            select(User)
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_users(self) -> list[User]:
        """Возвращает список пользователей без мягкого удаления."""

        stmt = (
            select(User)
            .where(User.deleted_at.is_(None))
            .order_by(User.id)
        )
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


