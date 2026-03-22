"""
Загрузка настроек из `.env` в корне репозитория (не из каталога fastapi/).

Все поля обязательны в .env — приложение не стартует с дефолтами «наугад».
Переменные вроде TEST_* лишние игнорируются (extra="ignore").
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Три уровня вверх: fastapi/src/utils → fastapi → корень проекта с .env
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Общие
    project_name: str
    environment: str

    # HTTP API (uvicorn)
    api_host: str
    api_port: int
    root_path: str = ""  # Префикс за reverse proxy, например /apps/em-auth

    # Postgres (дублируют часть DATABASE_URL, но удобны для Alembic/health)
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    database_url: str  # async SQLAlchemy, обычно postgresql+asyncpg://...

    # JWT и сессии
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    jwt_algorithm: str

    log_level: str


settings = Settings()
