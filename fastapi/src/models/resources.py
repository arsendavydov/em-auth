from sqlalchemy import Column, Integer, String

from src.models.base import Base


class Resource(Base):
    """ORM-модель ресурса, к которому применяются правила доступа."""

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(150), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
