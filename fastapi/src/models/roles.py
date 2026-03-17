from sqlalchemy import Column, Integer, String

from src.models.base import Base


class Role(Base):
    """ORM-модель роли пользователя в системе доступа."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

