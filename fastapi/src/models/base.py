from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData()


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""

    metadata = metadata
