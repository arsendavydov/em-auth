"""
Конфигурация Alembic: sync URL из настроек Postgres, target_metadata — все модели через Base.metadata.

Импорт `src.models.base` подтягивает регистрацию таблиц в metadata.
"""
from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
import sys

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from alembic import context

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.models import base  # noqa: F401
from src.models.base import metadata
from src.utils.config import settings


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sync_url = (
    f"postgresql+psycopg2://{settings.postgres_user}:"
    f"{settings.postgres_password}@{settings.postgres_host}:"
    f"{settings.postgres_port}/{settings.postgres_db}"
)

config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

