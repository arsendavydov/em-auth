from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import DatabaseError

from src.api.v1.access import router as access_v1_router
from src.api.v1.auth import router as auth_v1_router
from src.api.v1.health import router as health_v1_router
from src.api.v1.mock import router as mock_v1_router
from src.api.v1.users import router as users_v1_router
from src.exceptions.base import DomainException
from src.middleware.exception_handler import (
    database_exception_handler,
    domain_exception_handler,
    general_exception_handler,
)
from src.middleware.http_logging import HTTPLoggingMiddleware
from src.utils.config import settings
from src.utils.logger import get_logger, setup_logging
from src.utils.startup import shutdown_handler, startup_handler

setup_logging()
logger = get_logger(__name__)

API_DESCRIPTION = """
em-auth-service — backend-приложение для демонстрации собственной системы аутентификации
и авторизации поверх FastAPI и PostgreSQL.

Основные возможности:
- регистрация, login, refresh и logout;
- управление профилем пользователя и мягкое удаление аккаунта;
- ролевая модель доступа к пользователям;
- система правил доступа (RBAC) к mock-ресурсам;
- admin API для управления правилами доступа;
- health/readiness endpoints для проверки состояния приложения.

Технологии:
- FastAPI, Python 3.11, PostgreSQL 16, SQLAlchemy, Alembic;
- JWT, refresh tokens, bcrypt;
- nginx, Kubernetes (k3s), CI/CD (GitHub Actions).

Исходный код и документация: [github.com/arsendavydov/em-auth](https://github.com/arsendavydov/em-auth/)
""".strip()

OPENAPI_TAGS = [
    {"name": "health", "description": "Системные ручки для проверки состояния и готовности приложения."},
    {"name": "auth", "description": "Аутентификация пользователя, выдача и обновление токенов."},
    {"name": "users", "description": "Регистрация, профиль пользователя и операции с учетными записями."},
    {"name": "access", "description": "Административное управление ролями, ресурсами и правилами доступа."},
    {"name": "mock", "description": "Mock-ресурсы для демонстрации работы авторизации и RBAC."},
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Управляет запуском startup/shutdown hooks приложения."""

    await startup_handler()
    yield
    await shutdown_handler()


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI приложения."""

    app = FastAPI(
        title=settings.project_name,
        description=API_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
        root_path=settings.root_path,
        servers=[
            {
                "url": settings.root_path or "/apps/em-auth",
                "description": "Production server",
            },
        ],
    )
    app.add_middleware(HTTPLoggingMiddleware)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    app.include_router(health_v1_router, prefix="/api/v1")
    app.include_router(auth_v1_router, prefix="/api/v1")
    app.include_router(access_v1_router, prefix="/api/v1")
    app.include_router(mock_v1_router, prefix="/api/v1")
    app.include_router(users_v1_router, prefix="/api/v1")
    logger.info("Application configured")
    return app


app = create_app()

