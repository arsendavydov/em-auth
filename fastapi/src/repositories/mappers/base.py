"""
Базовый класс паттерна Data Mapper: ORM ↔ Pydantic без логики в моделях.

Конкретные мапперы — в том же пакете (например UsersMapper).
"""

from typing import Any, TypeVar

from sqlalchemy.orm import DeclarativeBase

OrmType = TypeVar("OrmType", bound=DeclarativeBase)
SchemaType = TypeVar("SchemaType")


class DataMapper[OrmType: DeclarativeBase, SchemaType]:
    """Базовый интерфейс Data Mapper для преобразования ORM-объектов и схем."""

    @staticmethod
    def to_schema(orm_obj: OrmType, **kwargs: Any) -> SchemaType:
        """Преобразует ORM-объект в схему ответа."""

        raise NotImplementedError("Подкласс должен реализовать to_schema()")

    @staticmethod
    def from_schema(
        schema_obj: SchemaType,
        exclude: set[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Преобразует схему запроса в словарь данных для ORM-модели."""

        raise NotImplementedError("Подкласс должен реализовать from_schema()")
