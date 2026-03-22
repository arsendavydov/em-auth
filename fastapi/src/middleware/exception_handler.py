from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError

from src.exceptions.base import DomainException
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def database_exception_handler(
    _request: Request,
    exc: DatabaseError,
) -> JSONResponse:
    """Преобразует ошибки базы данных в стандартизированные JSON-ответы."""

    logger.error(f"Database error: {exc}", exc_info=True)

    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Data integrity violation"},
        )

    if isinstance(exc, OperationalError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Database service is unavailable"},
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal database error"},
    )


async def domain_exception_handler(
    _request: Request,
    exc: DomainException,
) -> JSONResponse:
    """Преобразует доменные исключения приложения в JSON-ответ."""

    logger.error(f"Domain exception: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def general_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Обрабатывает необработанные исключения и возвращает безопасный ответ 500."""

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
