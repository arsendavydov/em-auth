from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.db import get_db

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Простая проверка состояния",
    description="Возвращает базовый статус приложения без углубленной диагностики зависимостей.",
)
async def health() -> dict:
    """Возвращает базовый health-статус приложения."""

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/ready",
    summary="Проверка готовности приложения",
    description=(
        "Проверяет, готово ли приложение принимать запросы. "
        "Для этого выполняется тестовый запрос к базе данных."
    ),
)
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Проверяет готовность приложения к обработке запросов.

    Args:
        db: Асинхронная сессия базы данных.

    Returns:
        Словарь со статусом готовности и временной меткой.
    """

    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc),
        }

