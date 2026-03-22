from sqlalchemy import Column, Integer, String

from src.models.base import Base


class Permission(Base):
    """ORM-модель действия (`permission`) в системе доступа."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
