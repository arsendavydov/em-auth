from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from src.models.base import Base


class RefreshToken(Base):
    """ORM-модель refresh token пользователя."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_revoked = Column(Boolean, default=False, nullable=False)
