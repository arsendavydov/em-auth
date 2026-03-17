from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_tokens import RefreshToken


class RefreshTokenRepository:
    """Репозиторий для работы с refresh токенами пользователя."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Создает и возвращает новый refresh token."""

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Возвращает активный и неистекший refresh token по его строковому значению."""

        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == token,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> None:
        """Отзывает один refresh token, если он существует и еще активен."""

        refresh_token = await self.get_by_token(token)
        if refresh_token is not None:
            refresh_token.is_revoked = True
            await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Отзывает все активные refresh токены указанного пользователя."""

        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
        await self.session.flush()

