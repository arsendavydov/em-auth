# Effective Mobile Test Task

Backend-приложение на `FastAPI` с собственной системой аутентификации и авторизации, построенной поверх `JWT`, `refresh tokens` и таблиц правил доступа в `PostgreSQL`.

## Выполнение задания

- ✅ Реализовано backend-приложение с собственной системой аутентификации и авторизации, не сводящейся к стандартной механике фреймворка.
- ✅ Реализован модуль взаимодействия с пользователем: регистрация, login, logout, обновление профиля, мягкое удаление аккаунта и запрет повторного входа после деактивации.
- ✅ После login пользователь идентифицируется по `JWT access token`, а для продолжения сессии реализован `refresh token` flow с отзывом токенов.
- ✅ Спроектирована и описана схема разграничения прав доступа, реализованы таблицы `roles`, `resources`, `permissions`, `access_rules`, `user_roles`, `refresh_tokens`.
- ✅ Реализован механизм авторизации для защищенных ресурсов с корректными `401` и `403` JSON-ответами.
- ✅ Реализован API для получения и изменения правил доступа пользователем с административной ролью.
- ✅ Реализованы минимальные mock-объекты бизнес-приложения без отдельных бизнес-таблиц, защищенные общей системой прав.
- ✅ Таблицы правил доступа и mock-разрешения заполнены начальными данными для демонстрации работы приложения.
- ✅ Все конфигурации, константы, секреты и подключения вынесены в `.env`, запуск выполняется из корня проекта.
- ✅ Подготовлены Docker-конфигурации для `local` и `prod` режимов с использованием `COMPOSE_BAKE=true`.
- ✅ E2E-тесты не зависят от состояния БД: создают пользователей в сценарии и затем удаляют их.
- ✅ Для модулей `fastapi/src` подготовлены unit-тесты с покрытием `100%`, а Swagger, докстринги, аннотации типов и обработка ошибок приведены к единообразному стилю.

Проект реализует:
- регистрацию, login, refresh и logout;
- мягкое удаление пользователя;
- ролевую модель доступа к пользователям;
- административное управление правилами доступа;
- mock-ресурсы для демонстрации работы авторизации;
- e2e и unit-тесты;
- `100%` покрытие `fastapi/src`.

## 1. Стек

- `Python 3.11`
- `FastAPI`
- `PostgreSQL 16`
- `SQLAlchemy 2`
- `Alembic`
- `PyJWT`
- `bcrypt`
- `nginx`
- `Docker` / `docker compose`
- `pytest`

## 2. Структура проекта

```text
.
├── .github
│   └── workflows
├── ci
│   ├── common
│   └── github
├── .env
├── .env.example
├── Dockerfile
├── Dockerfile.local
├── Dockerfile.prod
├── docker-compose.yml
├── docker-compose.local.yml
├── docker-compose.prod.yml
├── k3s
│   ├── fastapi-deployment.yaml
│   ├── fastapi-service.yaml
│   ├── ingress.yaml
│   ├── namespace.yaml
│   ├── nginx-configmap.yaml
│   ├── nginx-deployment.yaml
│   ├── nginx-service.yaml
│   └── postgres-statefulset.yaml
├── nginx
│   ├── Dockerfile
│   └── default.conf.template
├── backlog.md
├── todo.md
├── requirements.txt
├── README.md
└── fastapi
    ├── alembic.ini
    ├── pytest.ini
    ├── logs
    ├── scripts
    ├── src
    │   ├── api
    │   ├── exceptions
    │   ├── middleware
    │   ├── migrations
    │   ├── models
    │   ├── repositories
    │   ├── schemas
    │   ├── services
    │   └── utils
    └── tests
        ├── e2e_tests
        └── unit_tests
```

## 3. Конфигурация

Все реальные настройки и секреты хранятся в `.env`.

Пример:

```env
COMPOSE_BAKE=true

PROJECT_NAME=em-auth-service
ENVIRONMENT=local

API_HOST=0.0.0.0
API_PORT=8000
ROOT_PATH=

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=auth_db
POSTGRES_USER=db_admin
POSTGRES_PASSWORD=change_me_db_password

DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
TEST_DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}

SECRET_KEY=change_me_in_real_.env
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

LOG_LEVEL=info
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AUTH_PER_MINUTE=5
TEST_BASE_URL=http://localhost:8000
TEST_PASSWORD=test_password
```

Важно:
- приложение стартует только при наличии обязательных переменных окружения;
- Alembic берет реальные параметры подключения через `.env` в `fastapi/src/migrations/env.py`;
- `ROOT_PATH` используется для path-based deployment, например `/apps/em-auth` в production;
- `RATE_LIMIT_PER_MINUTE` и `RATE_LIMIT_AUTH_PER_MINUTE` используются `nginx` для ограничения запросов.

## 4. Запуск проекта

Все команды выполняются из корня проекта.

### Local mode

Для локальной разработки используется hot reload.

```bash
cp .env.example .env
COMPOSE_BAKE=true docker compose -f docker-compose.local.yml up -d --build
```

Что происходит:
- поднимается `postgres`;
- поднимается `fastapi`;
- поднимается `nginx` как внешний reverse proxy;
- перед запуском приложения накатываются миграции;
- `uvicorn` стартует в режиме `--reload`;
- наружу публикуется `nginx`, а `fastapi` доступен только внутри docker-сети.

Swagger:
- `http://localhost:8000/docs`
- `nginx` проксирует запросы на `fastapi`, поэтому внешний URL остаётся на порту `${API_PORT}`

### Prod mode

```bash
cp .env.example .env
COMPOSE_BAKE=true docker compose -f docker-compose.prod.yml up -d --build
```

В production-режиме:
- используется `Dockerfile.prod`;
- входящий трафик проходит через `nginx`;
- приложение стартует без hot reload;
- перед стартом также выполняются миграции.

### Production route

Планируемый production-маршрут в `k3s`:

- домен: `async-black.ru`
- path prefix: `/apps/em-auth`
- Swagger: `https://async-black.ru/apps/em-auth/docs#/`
- namespace: `em-auth`

Для этого в production используется `ROOT_PATH=/apps/em-auth`.

## 5. Миграции

Основные миграции:
- `20260316_0001_init_auth_schema.py`
- `20260316_0002_add_deleted_at_to_users.py`
- `20260317_0003_create_refresh_tokens.py`
- `20260317_0004_seed_mock_access_rules.py`

Ручной запуск миграций:

```bash
COMPOSE_BAKE=true docker compose -f docker-compose.local.yml exec fastapi alembic -c alembic.ini upgrade head
```

## 6. Архитектура

Проект построен по схеме:

`router -> service -> repository`

Роли слоев:
- `api/v1/*` — HTTP-роуты, Swagger и зависимости;
- `services/*` — бизнес-логика;
- `repositories/*` — работа с БД;
- `schemas/*` — Pydantic-схемы;
- `models/*` — SQLAlchemy ORM;
- `utils/*` — конфиг, auth, db, logger, startup;
- `middleware/*` — logging и exception handlers.

## 7. Схема данных

Основные таблицы:
- `users`
- `roles`
- `user_roles`
- `resources`
- `permissions`
- `access_rules`
- `refresh_tokens`

### Назначение таблиц

- `users` — учетные записи пользователей.
- `roles` — системные роли (`user`, `manager`, `admin`, `superadmin`).
- `user_roles` — связь many-to-many между пользователями и ролями.
- `resources` — коды ресурсов (`mock:projects:list`, `mock:reports:list`, ...).
- `permissions` — действия (`read`).
- `access_rules` — правило вида `role + resource + permission -> allow/deny`.
- `refresh_tokens` — выданные refresh token с возможностью revoke.

## 8. Аутентификация

Используется собственная схема:
- access token — `JWT`;
- refresh token — отдельная запись в БД;
- пароли хешируются через `bcrypt`;
- logout отзывает все refresh tokens пользователя;
- soft delete деактивирует пользователя и отзывает его refresh tokens.

### Поведение

- без токена — `401`
- невалидный токен — `401`
- пользователь определен, но не имеет прав — `403`

Все ответы API отдаются в JSON.

## 9. RBAC и правила доступа

Система прав построена на таблицах:
- `roles`
- `user_roles`
- `resources`
- `permissions`
- `access_rules`

Проверка доступа к ресурсам идет так:
1. определяется текущий пользователь по Bearer token;
2. подтягиваются его роли;
3. ищется разрешающее правило для комбинации:
   - пользователь
   - роль
   - ресурс
   - действие
4. если правило найдено — доступ разрешается;
5. если не найдено — возвращается `403`.

## 10. Матрица доступа к пользователям

| Роль | Видит пользователей | Изменяет пользователей | Мягко удаляет пользователей |
|------|----------------------|------------------------|-----------------------------|
| `user` | Только себя | Только себя | Только себя |
| `manager` | Всех, кроме `admin` и `superadmin` | Только себя | Только себя |
| `admin` | Всех | Себя и всех, кроме `admin` и `superadmin` | Себя и всех, кроме `admin` и `superadmin` |
| `superadmin` | Всех | Всех | Всех, кроме себя |

## 11. Матрица доступа к mock-ресурсам

| Роль | `mock:projects:list` | `mock:reports:list` | `mock:documents:list` |
|------|----------------------|---------------------|-----------------------|
| `user` | `read` | Нет | Нет |
| `manager` | `read` | `read` | Нет |
| `admin` | `read` | `read` | `read` |
| `superadmin` | `read` | `read` | `read` |

## 12. API

### Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Users

- `POST /api/v1/users/register`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `DELETE /api/v1/users/me`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

### Access admin API

- `GET /api/v1/access/roles`
- `GET /api/v1/access/resources`
- `GET /api/v1/access/permissions`
- `GET /api/v1/access/rules`
- `POST /api/v1/access/rules`
- `PATCH /api/v1/access/rules/{rule_id}`
- `DELETE /api/v1/access/rules/{rule_id}`

### Health

- `GET /api/v1/health`
- `GET /api/v1/ready`

### Mock resources

- `GET /api/v1/mock/projects`
- `GET /api/v1/mock/reports`
- `GET /api/v1/mock/documents`

## 13. Примеры запросов

### Регистрация

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@em.ru",
    "password": "test_password",
    "password_confirm": "test_password",
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович"
  }'
```

Пример ответа:

```json
{
  "email": "user@em.ru",
  "first_name": "Иван",
  "last_name": "Иванов",
  "middle_name": "Иванович",
  "id": 1,
  "is_active": true,
  "created_at": "2026-03-17T12:00:00+00:00",
  "updated_at": "2026-03-17T12:00:00+00:00",
  "deleted_at": null,
  "roles": []
}
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@em.ru",
    "password": "test_password"
  }'
```

Пример ответа:

```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "refresh_token_value",
  "token_type": "bearer"
}
```

### Refresh

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "refresh_token_value"
  }'
```

### Получить текущего пользователя

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer jwt_access_token"
```

### Получить mock-ресурс

```bash
curl -X GET "http://localhost:8000/api/v1/mock/projects" \
  -H "Authorization: Bearer jwt_access_token"
```

### Logout

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer jwt_access_token"
```

Пример ответа:

```json
{
  "status": "OK"
}
```

## 14. Тесты

### Запуск всех тестов

```bash
python3.11 -m pytest fastapi/tests
```

### Только unit

```bash
python3.11 -m pytest fastapi/tests/unit_tests
```

### Только e2e

```bash
python3.11 -m pytest fastapi/tests/e2e_tests
```

### Coverage

```bash
python3.11 -m pytest fastapi/tests --cov=fastapi/src --cov-report=term-missing
```

Текущее состояние:
- `73 passed`
- `fastapi/src` — `100% coverage`

## 15. Что важно про e2e

E2E-тесты не зависят от заранее заполненной БД:
- тесты сами создают пользователей;
- назначают роли через test DB helper;
- после завершения удаляют тестовые учетные записи;
- запуск возможен на пустой БД после миграций.

Для локального запуска с хоста используется:
- `TEST_BASE_URL`
- `TEST_DATABASE_URL`

## 16. Логирование

Подключено:
- логирование в stdout;
- логирование в файл `fastapi/logs/app.log`;
- ротация логов;
- опциональный JSON-формат через `LOG_FORMAT_JSON`.

HTTP access log пишется один раз через `src.middleware.http_logging`, без дублей через `root`.

## 17. Текущее состояние по заданию

Реализовано:
- собственная аутентификация;
- refresh/logout/revoke;
- soft delete пользователя;
- система ролей и правил доступа;
- admin API для изменения правил доступа;
- mock-ресурсы с проверкой прав;
- health/readiness;
- Docker local/prod;
- e2e и unit тесты;
- `100%` покрытие `fastapi/src`.

Осталось при желании:
- дополнять документацию;
- полировать UX Swagger и тексты ошибок;
- добавить дополнительные бизнес-ресурсы поверх текущего RBAC.
