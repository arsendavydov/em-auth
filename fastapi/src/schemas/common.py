from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Стандартный служебный ответ об успешном завершении операции."""

    status: str = Field(
        default="OK",
        description="Статус выполнения операции.",
        examples=["OK"],
    )

