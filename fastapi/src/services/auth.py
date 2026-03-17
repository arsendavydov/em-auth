from fastapi import HTTPException, status

from src.repositories.refresh_tokens import RefreshTokenRepository
from src.repositories.users import UserRepository
from src.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from src.utils.auth import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expires_at,
)
from src.utils.security import verify_password


class AuthService:
    """Сервис аутентификации и управления refresh токенами."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
        self.refresh_token_repository = RefreshTokenRepository(repository.session)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Аутентифицирует пользователя и выдает пару токенов.

        Args:
            data: Данные для входа пользователя.

        Returns:
            Пара access и refresh токенов.

        Raises:
            HTTPException: 401 если пользователь не найден, деактивирован или пароль неверен.
        """

        user = await self.repository.get_by_email(data.email)
        if user is None or user.deleted_at is not None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        roles = await self.repository.get_role_names(user.id)
        access_token = create_access_token(user_id=user.id, roles=roles)
        refresh_token = generate_refresh_token()
        expires_at = get_refresh_token_expires_at()

        await self.refresh_token_repository.create_token(user.id, refresh_token, expires_at)
        await self.repository.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, data: RefreshTokenRequest) -> TokenResponse:
        """
        Обновляет пару токенов по валидному refresh token.

        Args:
            data: Тело запроса с refresh token.

        Returns:
            Новая пара access и refresh токенов.

        Raises:
            HTTPException: 401 если refresh token невалиден или пользователь недоступен.
        """

        stored_token = await self.refresh_token_repository.get_by_token(data.refresh_token)
        if stored_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = await self.repository.get_by_id(stored_token.user_id)
        if user is None or user.deleted_at is not None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not available",
            )

        await self.refresh_token_repository.revoke_token(data.refresh_token)

        roles = await self.repository.get_role_names(user.id)
        access_token = create_access_token(user_id=user.id, roles=roles)
        refresh_token = generate_refresh_token()
        expires_at = get_refresh_token_expires_at()
        await self.refresh_token_repository.create_token(user.id, refresh_token, expires_at)
        await self.repository.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def logout(self, user_id: int) -> None:
        """
        Выполняет logout пользователя, отзывая все его refresh токены.

        Args:
            user_id: Идентификатор пользователя.
        """

        await self.refresh_token_repository.revoke_all_user_tokens(user_id)
        await self.repository.commit()

