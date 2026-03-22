"""
Хуки жизненного цикла приложения: проверка БД при старте, закрытие пула при остановке.

Вызываются из main.lifespan.
"""

from src.utils.db import check_connection, close_engine


async def startup_handler() -> None:
    """Выполняет startup-проверки приложения перед приемом запросов."""

    await check_connection()


async def shutdown_handler() -> None:
    """Выполняет корректное завершение инфраструктурных ресурсов приложения."""

    await close_engine()
