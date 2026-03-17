from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.utils.config import settings


engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Yield-генератор асинхронной сессии базы данных для FastAPI dependency."""

    async with AsyncSessionLocal() as session:
        yield session


async def check_connection() -> None:
    """Проверяет доступность базы данных тестовым запросом."""

    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))


async def close_engine() -> None:
    """Корректно закрывает SQLAlchemy engine при остановке приложения."""

    await engine.dispose()

