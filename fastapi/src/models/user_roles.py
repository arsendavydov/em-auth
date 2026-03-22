from sqlalchemy import Column, ForeignKey, Integer

from src.models.base import Base


class UserRole(Base):
    """Связующая ORM-модель между пользователями и ролями."""

    __tablename__ = "user_roles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
