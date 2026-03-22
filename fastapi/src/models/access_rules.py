from sqlalchemy import Boolean, Column, ForeignKey, Integer

from src.models.base import Base


class AccessRule(Base):
    """ORM-модель правила доступа для роли, ресурса и действия."""

    __tablename__ = "access_rules"

    # Связка «роль может/не может permission на resource»; is_allowed — итоговый флаг
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(
        Integer,
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_allowed = Column(Boolean, nullable=False, default=True)
