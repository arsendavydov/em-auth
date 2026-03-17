from typing import Any, Generic, TypeVar

from sqlalchemy.orm import DeclarativeBase

OrmType = TypeVar("OrmType", bound=DeclarativeBase)
SchemaType = TypeVar("SchemaType")


class DataMapper(Generic[OrmType, SchemaType]):
    """Базовый интерфейс Data Mapper для преобразования ORM-объектов и схем."""

    @staticmethod
    def to_schema(orm_obj: OrmType, **kwargs: Any) -> SchemaType:
        """Преобразует ORM-объект в схему ответа."""

        raise NotImplementedError("Method to_schema() must be implemented")

    @staticmethod
    def from_schema(
        schema_obj: SchemaType,
        exclude: set[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Преобразует схему запроса в словарь данных для ORM-модели."""

        raise NotImplementedError("Method from_schema() must be implemented")

