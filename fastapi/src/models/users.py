from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from src.models.base import Base


class User(Base):
    """ORM-модель пользователя системы."""

    __tablename__ = "users"

    # Идентификатор и учётные данные
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    middle_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt-хеш, не plaintext
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # мягкое удаление: не NULL → «удалён»
