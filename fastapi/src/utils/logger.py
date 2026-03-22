import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from src.utils.config import settings

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

TEXT_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5


def _use_json_logs() -> bool:
    """Определяет, нужно ли использовать JSON-формат логов."""

    value = os.getenv("LOG_FORMAT_JSON", "false").lower()
    return value in {"1", "true", "yes"}


class JsonFormatter(logging.Formatter):
    """Форматтер, сериализующий записи логов в JSON."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, DATE_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        return json.dumps(log_record, ensure_ascii=False)


def _create_handlers(
    log_file: Path,
    level: int,
) -> tuple[logging.FileHandler, logging.StreamHandler[Any]]:
    """Создает file и console handlers с единым форматированием."""

    formatter: logging.Formatter
    if _use_json_logs():
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(TEXT_LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
        delay=False,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    return file_handler, console_handler


def setup_logging(log_file_name: str = "app.log") -> None:
    """Настраивает root logger, системные логгеры и файловую ротацию логов."""

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_file = LOGS_DIR / log_file_name
    file_handler, console_handler = _create_handlers(log_file, level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    for logger_name in ["uvicorn", "uvicorn.error", "fastapi", "alembic"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.propagate = True

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.handlers.clear()
    sqlalchemy_logger.addHandler(file_handler)
    sqlalchemy_logger.addHandler(console_handler)
    sqlalchemy_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Возвращает именованный logger по имени модуля."""

    return logging.getLogger(name)
