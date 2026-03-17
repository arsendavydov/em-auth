from pydantic import BaseModel, Field


class MockProject(BaseModel):
    """Схема mock-проекта для демонстрации авторизации."""

    id: int = Field(description="Идентификатор mock-проекта.", examples=[1])
    name: str = Field(description="Название mock-проекта.", examples=["Mobile Banking"])
    status: str = Field(description="Текущий статус проекта.", examples=["active"])


class MockReport(BaseModel):
    """Схема mock-отчета для демонстрации авторизации."""

    id: int = Field(description="Идентификатор mock-отчета.", examples=[1])
    title: str = Field(description="Название отчета.", examples=["Weekly KPI"])
    period: str = Field(description="Период, к которому относится отчет.", examples=["2026-W11"])


class MockDocument(BaseModel):
    """Схема mock-документа для демонстрации авторизации."""

    id: int = Field(description="Идентификатор mock-документа.", examples=[1])
    filename: str = Field(description="Имя файла документа.", examples=["security-policy.pdf"])
    owner: str = Field(description="Владелец документа.", examples=["admin1@em.ru"])

