## Что сделано

### 1. Базовая инфраструктура проекта

- Выбран стек: `FastAPI + PostgreSQL + SQLAlchemy + Alembic + JWT`.
- Проект приведен к структуре, близкой к `Shum`:
  - `fastapi/src`
  - `fastapi/tests`
  - `fastapi/scripts`
  - внутри `src`: `api`, `models`, `schemas`, `repositories`, `repositories/mappers`, `services`, `utils`, `middleware`, `exceptions`, `migrations`.
- Старый пакет `app` удален, рабочий код живет в `fastapi/src`.
- Настроены:
  - `Dockerfile`
  - `docker-compose.yml`
  - сервисы `fastapi` и `postgres`
  - запуск из корня проекта
  - использование `COMPOSE_BAKE=true`

### 2. Конфигурация и окружение

- Созданы `.env` и `.env.example`.
- Все ключевые настройки вынесены в `.env`:
  - параметры API
  - параметры Postgres
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `REFRESH_TOKEN_EXPIRE_DAYS`
  - `JWT_ALGORITHM`
  - `LOG_LEVEL`
- Для локального прогона тестов с хоста добавлен `TEST_DATABASE_URL`.
- `fastapi/src/utils/config.py` сделан строгим:
  - без значений по умолчанию
  - без корректного `.env` приложение не должно стартовать
  - обязательные настройки приложения валидируются явно
  - лишние переменные окружения (`TEST_*`, `COMPOSE_BAKE`) не ломают импорт приложения

### 3. База данных и миграции

- Настроен Alembic в `fastapi/alembic.ini`.
- Настроен `fastapi/src/migrations/env.py`.
- Созданы и заведены миграции:
  - `20260316_0001_init_auth_schema.py`
  - `20260316_0002_add_deleted_at_to_users.py`
  - `20260317_0003_create_refresh_tokens.py`
  - `20260317_0004_seed_mock_access_rules.py`
- В модели `users` есть:
  - `created_at`
  - `updated_at`
  - `deleted_at`
- Основные таблицы проекта:
  - `users`
  - `roles`
  - `user_roles`
  - `resources`
  - `permissions`
  - `access_rules`
  - `refresh_tokens`

### 4. Модели

- Реализованы ORM-модели:
  - `User`
  - `Role`
  - `UserRole`
  - `Resource`
  - `Permission`
  - `AccessRule`
  - `RefreshToken`
- Для soft delete в `User` используются:
  - `is_active`
  - `deleted_at`

### 5. Аутентификация и безопасность

- Реализовано хеширование паролей на чистом `bcrypt`, без `passlib`.
- Реализован JWT access token.
- Реализован refresh token flow:
  - login
  - refresh
  - logout
- Реализован отзыв refresh токенов:
  - отзыв одного refresh token при `refresh`
  - отзыв всех refresh tokens пользователя при `logout`
  - отзыв всех refresh tokens пользователя при soft delete
- Добавлены:
  - `src/utils/auth.py`
  - `src/services/auth.py`
  - `src/repositories/refresh_tokens.py`

### 6. Пользовательский API

- Реализованы ручки:
  - `POST /api/v1/users/register`
  - `GET /api/v1/users/me`
  - `PATCH /api/v1/users/me`
  - `DELETE /api/v1/users/me`
  - `GET /api/v1/users`
  - `GET /api/v1/users/{user_id}`
  - `PATCH /api/v1/users/{user_id}`
  - `DELETE /api/v1/users/{user_id}`
- Реализованы ручки auth:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
- Реализована dependency текущего пользователя:
  - `get_current_user`

### 7. Ролевая матрица пользователей

- Зафиксирована логика ролей:
  - `user`
  - `manager`
  - `admin`
  - `superadmin`
- Реализованы правила просмотра / изменения / удаления пользователей:
  - `user` видит и меняет только себя
  - `manager` видит всех, кроме `admin` и `superadmin`, меняет только себя
  - `admin` видит всех, меняет себя и всех, кроме других `admin` и `superadmin`
  - `admin` может удалить себя и пользователей ниже, но не других `admin` и не `superadmin`
  - `superadmin` видит всех и меняет всех, но не может удалить самого себя

### 8. Тестовые данные в БД

- На раннем этапе через `psql` заводились тестовые пользователи:
  - `admin1@em.ru`
  - `admin2@em.ru`
  - `manager1@em.ru`
  - `manager2@em.ru`
  - `user1@em.ru`
  - `user2@em.ru`
- Для них назначались роли в `user_roles`.
- Использовался общий тестовый пароль:
  - `test_password`
- Эти данные больше не являются обязательными для e2e-прогонов.

### 9. Тестовые пользователи

- Добавлены e2e-фикстуры, которые создают пользователей прямо во время теста.
- Для e2e используется фабрика аккаунтов с автоматическим созданием:
  - `admin`
  - `manager`
  - `user`
- Роли тестовым пользователям назначаются напрямую через тестовый DB helper.
- После завершения сценария тестовые пользователи физически удаляются из БД.
- Благодаря этому e2e больше не зависят от заранее заполненной базы и могут запускаться на пустой БД после миграций.

### 10. Data Mapper pattern

- Добавлен паттерн `repositories/mappers`, как в `Shum`.
- Реализованы:
  - `DataMapper`
  - `UsersMapper`
- `UserService` частично переведен на маппер:
  - сборка `UserRead`
  - преобразование create/update данных

### 11. Health checks и startup-проверки

- Добавлен `lifespan` в `main.py`.
- На старте приложения выполняется проверка БД:
  - `startup_handler()`
  - `check_connection()`
- На shutdown закрывается SQLAlchemy engine.
- Добавлены ручки:
  - `GET /api/v1/health`
  - `GET /api/v1/ready`

### 12. Логирование и обработка ошибок

- Добавлен модуль логирования:
  - `src/utils/logger.py`
- Подключено:
  - логирование в stdout
  - логирование в файл
  - rotation логов
  - optional JSON logs
- Добавлен middleware:
  - `src/middleware/http_logging.py`
- Убрано дублирование access-логов:
  - HTTP-запрос теперь логируется один раз через `src.middleware.http_logging`
  - лишняя повторная запись того же сообщения в `root` удалена
- Добавлены global exception handlers:
  - `DatabaseError`
  - `DomainException`
  - `Exception`
- Добавлена общая схема успешного служебного ответа:
  - `MessageResponse`
  - формат в стиле `Shum`: `{"status": "OK"}`

### 13. Mock-ресурсы для демонстрации авторизации

- Добавлены mock endpoint-ы:
  - `GET /api/v1/mock/projects`
  - `GET /api/v1/mock/reports`
  - `GET /api/v1/mock/documents`
- Эти ручки не используют отдельные бизнес-таблицы и нужны для демонстрации работы авторизации на ресурсах.
- Реализован permission-слой через БД:
  - `src/repositories/access_control.py`
  - `src/utils/permissions.py`
- Проверка идет через таблицы:
  - `roles`
  - `user_roles`
  - `resources`
  - `permissions`
  - `access_rules`

### 14. Права на mock-ресурсы

- Подготовлена миграция сидирования mock access rules:
  - `20260317_0004_seed_mock_access_rules.py`
- Логика доступа:
  - `user` -> `mock:projects:list`
  - `manager` -> `mock:projects:list`, `mock:reports:list`
  - `admin` -> `mock:projects:list`, `mock:reports:list`, `mock:documents:list`
  - `superadmin` -> все mock-ресурсы

### 15. Общая матрица прав

| Роль | Видит пользователей | Изменяет пользователей | Мягко удаляет пользователей | Mock projects | Mock reports | Mock documents |
|------|----------------------|------------------------|-----------------------------|---------------|--------------|----------------|
| `user` | Только себя | Только себя | Только себя | Да | Нет | Нет |
| `manager` | Всех, кроме `admin` и `superadmin` | Только себя | Только себя | Да | Да | Нет |
| `admin` | Всех, включая себя и `superadmin` | Себя + всех, кроме других `admin` и `superadmin` | Себя + всех, кроме других `admin` и `superadmin` | Да | Да | Да |
| `superadmin` | Всех | Всех | Всех, кроме себя | Да | Да | Да |

### 16. Что уже точно применено/сделано руками

- Контейнеры `fastapi` и `postgres` поднимались и пересобирались.
- Создавались/правились роли Postgres:
  - `db_admin`
- Накатывались ранние миграции.
- Проверялась доступность OpenAPI.
- Проверялось наличие пользовательских ручек в Swagger / OpenAPI.
- Полностью удалена роль `auth_user`, приложение и миграции работают через `db_admin`.

### 17. Что нужно держать в голове

- Для локальной разработки есть отдельный dev-режим:
  - `Dockerfile.local`
  - `docker-compose.local.yml`
  - hot reload через `uvicorn --reload`
- Для production подготовлены:
  - `Dockerfile.prod`
  - `docker-compose.prod.yml`
- В `docker-compose.local.yml` убран обязательный автосид тестовых пользователей на старте.
- Для актуального локального прогона:
  - миграций достаточно
  - e2e сами создают нужные учетные записи
- Для локального запуска тестов с хоста нужно использовать `python3.12` (или venv на 3.12), а не системный `pytest` на старом Python.

### 18. Админ API для правил доступа

- Реализован admin API для управления RBAC-слоем:
  - `GET /api/v1/access/roles`
  - `GET /api/v1/access/resources`
  - `GET /api/v1/access/permissions`
  - `GET /api/v1/access/rules`
  - `POST /api/v1/access/rules`
  - `PATCH /api/v1/access/rules/{rule_id}`
  - `DELETE /api/v1/access/rules/{rule_id}`
- Добавлены:
  - `src/repositories/access_admin.py`
  - `src/services/access.py`
  - `src/api/v1/access.py`
- Изменение правил доступа ограничено пользователями с ролью `admin` или `superadmin`.

### 19. Docker-режимы local/prod

- Подготовлены отдельные режимы запуска:
  - `docker-compose.local.yml` для локальной разработки
  - `docker-compose.prod.yml` для production
- В local-режиме:
  - используется bind mount
  - изменения в `fastapi/src` подхватываются без ручного рестарта
- Добавлен `.dockerignore` для сокращения docker build context.

### 20. E2E-тесты

- Написаны полноценные e2e-тесты:
  - `test_auth_lifecycle.py`
  - `test_user_permissions.py`
  - `test_access_admin_flow.py`
- Покрыты сценарии:
  - регистрация
  - login
  - refresh
  - logout
  - soft delete
  - visibility/update/delete пользователей по ролям
  - admin flow для `access_rules`
  - реальная проверка доступа к mock-ресурсам
- `fastapi/tests/conftest.py` оставлен нейтральным для unit-тестов.
- E2E-фикстуры вынесены в `fastapi/tests/e2e_tests/conftest.py`.

### 21. Unit-тесты и покрытие

- Существенно расширен набор unit-тестов.
- Добавлены тесты для:
  - `services/users.py`
  - `services/auth.py`
  - `services/access.py`
  - `utils/auth.py`
  - `utils/permissions.py`
  - `utils/db.py`
  - `utils/logger.py`
  - `utils/startup.py`
  - `repositories/users.py`
  - `repositories/refresh_tokens.py`
  - `repositories/access_admin.py`
  - `repositories/access_control.py`
  - `repositories/mappers/base.py`
  - `main.py`
  - `api/v1/*`
  - middleware и exception handlers
- Итоговый прогон:
  - `python3.12 -m pytest fastapi/tests --cov=fastapi/src --cov-report=term-missing`
- Текущий статус:
  - `73 passed`
  - `fastapi/src`: `100% coverage`

### 22. Обновление тестового стека

- Для анализа покрытия установлен `pytest-cov`.
- Обновлен `FastAPI`:
  - `0.115.0 -> 0.135.1`
- Вместе с ним обновлен `Starlette`:
  - `0.38.6 -> 0.52.1`
- После обновления ушел warning из старого импорта `python-multipart` в тестах.

### 23. Единообразие кода и Swagger

- Публичный API-слой приведен ближе к стилю `Shum`.
- Для роутов `api/v1/*` добавлены:
  - `summary`
  - `description`
  - русские docstring
  - явные аннотации возвращаемых типов
- Для ключевых ручек в Swagger добавлены `responses=` для основных сценариев:
  - `400`
  - `401`
  - `403`
  - `404`
  - `409`
- В `main.py` добавлены:
  - `API_DESCRIPTION`
  - `openapi_tags`
- Обновлены Pydantic-схемы:
  - `schemas/users.py`
  - `schemas/auth.py`
  - `schemas/access.py`
  - `schemas/mock.py`
  - `schemas/common.py`
- Для полей схем добавлены:
  - `description`
  - `examples`
  - ограничения валидации там, где они логически нужны

### 24. Докстринги и аннотации типов

- Добавлены русские docstring в:
  - `services/*`
  - `repositories/*`
  - `utils/*`
  - `middleware/*`
  - `models/*`
  - `exceptions/base.py`
- Выравнен стиль сигнатур:
  - явные return types
  - типизированные dependency factory-функции
  - современный синтаксис типов Python 3.12

### 25. Логирование и конфигурационные мелочи

- Убрано дублирование HTTP access-логов:
  - запрос логируется один раз через `src.middleware.http_logging`
  - повторная запись в `root` удалена
- `fastapi/alembic.ini` очищен от визуального хардкода:
  - вместо реального URL оставлен нейтральный placeholder
  - фактический sync URL для Alembic по-прежнему собирается через `.env` в `src/migrations/env.py`
- Реальные значения подключения к БД и секреты остаются только в `.env`.

### 26. README выровнен под формулировки ТЗ

- В начало `README.md` добавлен отдельный чек-лист выполнения задания.
- Пункты чек-листа переформулированы максимально близко к исходному тексту ТЗ:
  - собственная аутентификация и авторизация
  - взаимодействие с пользователем
  - идентификация после login
  - система разграничения прав доступа
  - admin API для изменения правил
  - mock-объекты бизнес-приложения
  - конфигурация через `.env`
  - docker local/prod режимы
  - независимые e2e и полное unit-покрытие
- Напротив каждого пункта добавлен статус выполнения через зеленый чекбокс `✅`.
- За счет этого `README.md` теперь можно использовать как короткую сверку результата с требованиями задания уже с первых строк документа.

### 27. Подготовка приложения к path-based deploy

- В конфигурацию приложения добавлен `ROOT_PATH`.
- `fastapi/src/main.py` обновлен так, чтобы `FastAPI` создавался с `root_path=settings.root_path`.
- `fastapi/src/utils/config.py` больше не зависит от текущего `working_dir` контейнера:
  - `.env` теперь ищется от корня проекта
  - это устраняет расхождения между локальным запуском и docker/k8s-окружением
- В `.env.example` добавлены:
  - `ROOT_PATH`
  - `RATE_LIMIT_PER_MINUTE`
  - `RATE_LIMIT_AUTH_PER_MINUTE`
- Под целевой production-маршрут зафиксирован путь:
  - `https://async-black.ru/apps/em-auth/docs#/`

### 28. Введение nginx по аналогии с Shum

- Добавлена директория `nginx/`.
- Созданы:
  - `nginx/Dockerfile`
  - `nginx/default.conf.template`
- В `docker-compose.local.yml` и `docker-compose.prod.yml` добавлен сервис `nginx`.
- Теперь во внешнюю сеть публикуется `nginx`, а `fastapi` остается внутренним сервисом docker-сети.
- В `nginx` настроены:
  - reverse proxy на `fastapi`
  - прокидывание `X-Real-IP`, `X-Forwarded-*`, `Host`
  - health endpoint `/health`
  - JSON access log
  - gzip
  - security headers
  - rate limiting по аналогии с `Shum`
- Ограничены чувствительные ручки:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/users/register`
- Для превышения лимита настроен JSON-ответ `429`.

### 29. Подготовка k3s / CI / GitHub Actions

- Добавлена директория `k3s/` с минимальным набором production-манифестов:
  - `namespace.yaml`
  - `fastapi-deployment.yaml`
  - `fastapi-service.yaml`
  - `nginx-configmap.yaml`
  - `nginx-deployment.yaml`
  - `nginx-service.yaml`
  - `postgres-statefulset.yaml`
  - `ingress.yaml`
- Для Kubernetes выделен отдельный namespace:
  - `em-auth`
- В `Ingress` заложен path-based deploy:
  - `host = async-black.ru`
  - `path = /apps/em-auth(/|$)(.*)`
  - rewrite по аналогии с `Shum`
- Добавлены директории и файлы под CI/CD:
  - `.github/workflows/deploy.yml`
  - `ci/helpers.sh`
  - `ci/get-kubeconfig.sh`
  - `ci/create-configmap-and-secret.sh`
  - `ci/apply-manifests.sh`
  - `ci/common/check-active-provider.sh`
  - `ci/README.md`
  - `ci/github/README.md`
- `GitHub Actions` workflow подготовлен по мотивам `Shum`:
  - checkout
  - venv `.venv312`, `pip install -r requirements.txt`
  - unit tests (`pytest fastapi/tests/unit_tests`)
  - **линтеры перед деплоем**: `ruff check`, `ruff format --check`, `pyright` (каталог `fastapi/`)
  - сборка и push образов `fastapi` и `nginx`
  - подготовка SSH ключа
  - получение kubeconfig с сервера
  - создание/обновление `ConfigMap` и `Secret`
  - `kubectl apply` манифестов
  - проверка rollout
- CI-логика адаптирована под текущий проект:
  - без `celery`
  - без `redis`
  - с namespace `em-auth`
  - с маршрутом `/apps/em-auth`

### 30. Что осталось доделать

- При желании добавить в `README.md` примеры запросов:
  - регистрация
  - login / refresh / logout
  - работа с `/users`
  - работа с `/access`
  - работа с `/mock/*`
- При желании расширить `README.md` про:
  - local docker mode (кратко уже есть через compose + lint)
  - unit/e2e тесты (команды можно продублировать одной строкой в начале README)
- При желании добавить отдельную удобную команду/скрипт для запуска всех тестов и coverage из корня проекта.

### 31. Отдельный production env для em-auth

- Принято решение не использовать общий `~/.prod.env` вместе с `Shum`.
- Для нового сервиса выделен отдельный server-side env-файл:
  - `/home/k3s-admin/.prod.env.em-auth`
- Обновлены `ci`-скрипты и `GitHub Actions`, чтобы они читали именно этот файл.
- В репозиторий добавлен шаблон:
  - `em-auth.prod.env.example`
- В `README.md` и `ci`-документации отражено, что `Shum` и `em-auth` должны хранить production env раздельно.

### 32. Управление ролями пользователей и финальная полировка API/документации

- Добавлены методы управления ролями пользователей:
  - `POST /api/v1/users/{user_id}/roles/{role_name}`
  - `DELETE /api/v1/users/{user_id}/roles/{role_name}`
- Реализована логика сервиса:
  - `_ensure_can_manage_roles` с иерархией `user < manager < admin < superadmin`;
  - `assign_role` и `remove_role` с проверкой существования роли и запретом небезопасных операций.
- Расширен `UserRepository` методами:
  - `get_role_by_name`
  - `add_user_role`
  - `remove_user_role`
- Добавлены unit-тесты для:
  - `_ensure_can_manage_roles` (позитивные и негативные сценарии);
  - `assign_role` и `remove_role`.
- Добавлен e2e-тест `test_user_roles_management.py`, проверяющий:
  - возможность супер-админа назначать роли;
  - ограничения для админа при работе с ролью `superadmin`.
- Поведение регистрации пользователя изменено:
  - при успешной регистрации по умолчанию пытаемся выдать роль `user`;
  - при отсутствии роли `user` в БД регистрация не ломается.
- Обновлен e2e-тест `test_auth_lifecycle.py`:
  - теперь ожидает, что у свежезарегистрированного пользователя роль `["user"]`.
- Swagger / OpenAPI:
  - описание `API_DESCRIPTION` приведено к более полному формату (основные возможности + технологии);
  - добавлен раздел «Технологии» с перечислением стека;
  - добавлены `servers` в `FastAPI(...)`:
    - `url = settings.root_path или "/apps/em-auth"`
    - `description = "Production server"`
  - в UI Swagger для `em-auth` теперь отображается сервер `/apps/em-auth - Production server`, как в `Shum`.
- README упрощен и приведен к виду «как в проде»:
  - оставлены только ключевые пункты выполнения задания;
  - добавлен краткий список таблиц БД (`users`, `roles`, `user_roles`, `resources`, `permissions`, `access_rules`, `refresh_tokens`);
  - ссылка на репозиторий оформлена как кликабельная гиперссылка.
- Лишние prod-конфиги docker-compose удалены:
  - `docker-compose.prod.yml` убран, т.к. production-деплой реализован через `k3s` и `GitHub Actions`.
- В прод-среде:
  - назначена роль `superadmin` пользователю `superadmin@em.ru` напрямую через БД;
  - через новые API-ручки разданы роли:
    - `admin1@em.ru`, `admin2@em.ru` → `admin`
    - `manager1@em.ru`, `manager2@em.ru` → `manager`
    - `user1@em.ru`, `user2@em.ru` → `user`
  - старые учетные записи `manager*/user*@async-black.ru` мягко удалены через `DELETE /api/v1/users/me`.

### 33. Python 3.12, Ruff/Pyright, правки под ревью и Docker local

- **Версия Python**: локально, в `Dockerfile.prod` / `Dockerfile.local`, в GitHub Actions (`setup-python`) и в описании API — **Python 3.12** (образ `python:3.12-slim`).
- **Устаревший `datetime.utcnow()`** заменён на **`datetime.now(timezone.utc)`** в:
  - `fastapi/src/api/v1/health.py`
  - `fastapi/tests/unit_tests/test_users_service.py`
- **Линтинг и форматирование (по аналогии с Shum)**:
  - в `requirements.txt` добавлены `ruff`, `pyright`;
  - конфиг **`fastapi/pyproject.toml`**: `[tool.ruff]`, `[tool.pyright]` (venv для Pyright в IDE/локально: **`../.venv312`** относительно `fastapi/`);
  - скрипт **`fastapi/scripts/lint.sh`**:
    - `check` / `fix` — через `docker compose -f docker-compose.local.yml exec fastapi` (`python -m ruff`, `python -m pyright`);
    - `check-local` / `fix-local` — без Docker, через `.venv312/bin/python` в корне репозитория;
  - правки кода под Ruff: форматирование, импорты, удалён бессмысленный `except` в `http_logging`, типизация mock-ответов в `api/v1/mock.py`, аннотация `get_db` как `AsyncGenerator`, и т.д.;
  - для FastAPI-роутов с `Depends(...)` добавлен **per-file ignore `ARG001`** на `src/api/**/*.py` (аргумент только ради side-effect авторизации).
- **Docker local для Pyright**: в **`Dockerfile.local`** установлен пакет **`libatomic1`** — иначе в slim-образе падает Node, который подтягивает `pyright-python`.
- **`docker-compose.local.yml`**: убран устаревший ключ **`version:`** (предупреждение Compose v2).
- **CI**: шаг «Run unit tests and linters» в `.github/workflows/deploy.yml` гоняет тесты и линтеры **до** сборки образов и выката в k3s; при падении lint — деплой не выполняется.
- **Документация**: в `README.md` описаны команды линтера, CI-gate и зависимость образа от `libatomic1` для Pyright в контейнере.

