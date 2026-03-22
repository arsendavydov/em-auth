from datetime import UTC, datetime

from fastapi import HTTPException, status

from src.models.users import User
from src.repositories.mappers.users_mapper import UsersMapper
from src.repositories.refresh_tokens import RefreshTokenRepository
from src.repositories.users import UserRepository
from src.schemas.users import UserCreate, UserRead, UserUpdate
from src.utils.auth import RequestUser
from src.utils.security import hash_password


class UserService:
    """Сервис управления пользователями и проверками ролевых ограничений."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
        self.refresh_token_repository = RefreshTokenRepository(repository.session)

    async def _build_user_read(self, user: User) -> UserRead:
        """Собирает `UserRead` с подгрузкой ролей пользователя."""

        roles = await self.repository.get_role_names(user.id)
        return UsersMapper.to_schema(user, roles=roles)

    async def _get_target_or_404(self, user_id: int) -> User:
        """Возвращает пользователя по ID или поднимает 404 для отсутствующего/удаленного пользователя."""

        target = await self.repository.get_by_id(user_id)
        if target is None or target.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return target

    async def _ensure_email_is_free(
        self,
        email: str | None,
        current_user_id: int | None = None,
    ) -> None:
        """Проверяет, что email свободен или принадлежит текущему редактируемому пользователю."""

        if email is None:
            return

        existing = await self.repository.get_by_email(email)
        if existing and existing.id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    async def _can_view_user(self, actor: RequestUser, target: User) -> bool:
        """Возвращает `True`, если текущий пользователь может просматривать целевого пользователя."""

        if actor.id == target.id:
            return True
        if actor.has_role("superadmin"):
            return True
        if actor.has_role("admin"):
            return True
        if actor.has_role("manager"):
            target_roles = await self.repository.get_role_names(target.id)
            return "admin" not in target_roles and "superadmin" not in target_roles
        return False

    async def _ensure_can_update_user(self, actor: RequestUser, target: User) -> None:
        """Проверяет, что текущий пользователь может изменять целевого пользователя."""

        if actor.id == target.id:
            return
        if actor.has_role("superadmin"):
            return
        if actor.has_role("admin"):
            target_roles = await self.repository.get_role_names(target.id)
            if "admin" in target_roles or "superadmin" in target_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admins cannot update other admins or superadmins",
                )
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update this user",
        )

    async def _ensure_can_delete_user(self, actor: RequestUser, target: User) -> None:
        """Проверяет, что текущий пользователь может мягко удалить целевого пользователя."""

        if actor.has_role("superadmin"):
            if actor.id == target.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Superadmin cannot delete themselves",
                )
            return

        if actor.has_role("admin"):
            if actor.id == target.id:
                return
            target_roles = await self.repository.get_role_names(target.id)
            if "admin" in target_roles or "superadmin" in target_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admins cannot delete other admins or superadmins",
                )
            return

        if actor.id == target.id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete this user",
        )

    async def _ensure_can_manage_roles(
        self,
        actor: RequestUser,
        target: User,
        role_name: str,
    ) -> None:
        """
        Проверяет, что текущий пользователь может назначать или отзывать роли целевого пользователя.

        Правила:
        * Только пользователи с ролями `admin` или `superadmin` могут управлять ролями.
        * Операции с ролью `superadmin` доступны только пользователю с ролью `superadmin`.
        * Пользователь с ролью `admin` не может управлять ролями пользователей, у которых уже есть
          роли `admin` или `superadmin`.
        """

        actor_roles = actor.roles
        if "superadmin" not in actor_roles and "admin" not in actor_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot manage roles for this user",
            )

        normalized_role = role_name.lower()
        if normalized_role == "superadmin" and "superadmin" not in actor_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin can manage superadmin role",
            )

        target_roles = await self.repository.get_role_names(target.id)

        if "superadmin" in target_roles and "superadmin" not in actor_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin can manage roles of another superadmin",
            )

        if "admin" in target_roles and "superadmin" not in actor_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot manage roles of other admins",
            )

    async def register_user(self, data: UserCreate) -> UserRead:
        """
        Регистрирует нового пользователя.

        Raises:
            HTTPException: 400 если пароли не совпадают или email уже занят.
        """

        if data.password != data.password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        await self._ensure_email_is_free(data.email)

        user_data = UsersMapper.from_schema(
            data,
            exclude={"password", "password_confirm"},
            password_hash=hash_password(data.password),
        )
        user = User(**user_data)
        user = await self.repository.add(user)

        # Пытаемся по умолчанию выдать пользователю роль `user`.
        # Если роль отсутствует в БД, регистрация все равно считается успешной.
        default_role = await self.repository.get_role_by_name("user")
        if default_role is not None:
            await self.repository.add_user_role(user.id, default_role.id)

        await self.repository.commit()
        return await self._build_user_read(user)

    async def get_me(self, actor: RequestUser) -> UserRead:
        """Возвращает профиль текущего пользователя."""

        return await self._build_user_read(actor.user)

    async def get_user(self, actor: RequestUser, user_id: int) -> UserRead:
        """
        Возвращает пользователя по идентификатору с учетом правил видимости.

        Raises:
            HTTPException: 403 если у текущего пользователя нет права на просмотр.
            HTTPException: 404 если пользователь не найден.
        """

        target = await self._get_target_or_404(user_id)
        if not await self._can_view_user(actor, target):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view this user",
            )
        return await self._build_user_read(target)

    async def list_users(self, actor: RequestUser) -> list[UserRead]:
        """Возвращает список пользователей, доступных текущему пользователю."""

        users = await self.repository.list_active_users()
        visible_users: list[UserRead] = []
        for user in users:
            if await self._can_view_user(actor, user):
                visible_users.append(await self._build_user_read(user))
        return visible_users

    async def update_user(
        self,
        actor: RequestUser,
        user_id: int,
        data: UserUpdate,
    ) -> UserRead:
        """
        Обновляет пользователя с учетом ролевых ограничений.

        Raises:
            HTTPException: 400 если новый email уже занят.
            HTTPException: 403 если обновление запрещено ролью.
            HTTPException: 404 если пользователь не найден.
        """

        target = await self._get_target_or_404(user_id)
        await self._ensure_can_update_user(actor, target)
        await self._ensure_email_is_free(data.email, current_user_id=target.id)

        update_data = UsersMapper.from_schema(data)
        for field, value in update_data.items():
            setattr(target, field, value)

        await self.repository.commit()
        refreshed_target = await self._get_target_or_404(target.id)
        return await self._build_user_read(refreshed_target)

    async def soft_delete_user(self, actor: RequestUser, user_id: int) -> None:
        """
        Выполняет мягкое удаление пользователя и отзыв всех его refresh токенов.

        Raises:
            HTTPException: 403 если удаление запрещено ролью.
            HTTPException: 404 если пользователь не найден.
        """

        target = await self._get_target_or_404(user_id)
        await self._ensure_can_delete_user(actor, target)

        target.is_active = False
        target.deleted_at = datetime.now(UTC)

        await self.refresh_token_repository.revoke_all_user_tokens(target.id)
        await self.repository.commit()

    async def assign_role(
        self,
        actor: RequestUser,
        user_id: int,
        role_name: str,
    ) -> UserRead:
        """
        Назначает пользователю роль с учетом ролевых ограничений.

        Raises:
            HTTPException: 403 если операция запрещена.
            HTTPException: 404 если пользователь или роль не найдены.
        """

        target = await self._get_target_or_404(user_id)
        normalized_role = role_name.lower()
        await self._ensure_can_manage_roles(actor, target, normalized_role)

        role = await self.repository.get_role_by_name(normalized_role)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        await self.repository.add_user_role(target.id, role.id)
        await self.repository.commit()
        refreshed_target = await self._get_target_or_404(target.id)
        return await self._build_user_read(refreshed_target)

    async def remove_role(
        self,
        actor: RequestUser,
        user_id: int,
        role_name: str,
    ) -> UserRead:
        """
        Удаляет роль пользователя с учетом ролевых ограничений.

        Raises:
            HTTPException: 403 если операция запрещена.
            HTTPException: 404 если пользователь или роль не найдены.
        """

        target = await self._get_target_or_404(user_id)
        normalized_role = role_name.lower()
        await self._ensure_can_manage_roles(actor, target, normalized_role)

        role = await self.repository.get_role_by_name(normalized_role)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        removed = await self.repository.remove_user_role(target.id, role.id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not have this role",
            )

        await self.repository.commit()
        refreshed_target = await self._get_target_or_404(target.id)
        return await self._build_user_read(refreshed_target)
