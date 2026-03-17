## Effective Mobile — em-auth-service

Backend-приложение на `FastAPI` и `PostgreSQL` с собственной системой аутентификации и авторизации, построенной поверх `JWT`, `refresh tokens` и таблиц правил доступа в БД.

Репозиторий: https://github.com/arsendavydov/em-auth/

### Выполнение задания (кратко)

- ✅ Собственная аутентификация: регистрация, login, refresh, logout, мягкое удаление пользователя.
- ✅ Ролевая модель (`user`, `manager`, `admin`, `superadmin`) и таблицы `roles`, `user_roles`, `resources`, `permissions`, `access_rules`, `refresh_tokens`.
- ✅ Авторизация к защищенным ресурсам с корректными `401` / `403` JSON-ответами.
- ✅ Admin API для управления правилами доступа.
- ✅ Mock-ресурсы для демонстрации работы системы прав.
- ✅ Все настройки и секреты вынесены в `.env`, запуск из корня проекта.
- ✅ E2E-тесты независимы от состояния БД, `fastapi/src` покрыт unit-тестами на 100%.

### Стек

- `Python 3.11`, `FastAPI`, `PostgreSQL 16`, `SQLAlchemy 2`, `Alembic`
- `PyJWT`, `bcrypt`
- `nginx` (reverse proxy, rate limiting)
- `Docker` / `docker compose` (local)
- `k3s` + `GitHub Actions` (production deploy)

### Запуск локально

Все команды — из корня проекта.

1. Скопировать пример окружения:

```bash
cp .env.example .env
```

2. Поднять локальный стек (`fastapi` + `postgres` + `nginx`) с hot reload:

```bash
COMPOSE_BAKE=true docker compose -f docker-compose.local.yml up -d --build
```

3. Swagger и API:

- Swagger UI: `http://localhost:8000/docs`
- API: `http://localhost:8000/api/v1/...`

### Production (k3s)

- Домен: `async-black.ru`
- Path prefix: `/apps/em-auth`
- Swagger: `https://async-black.ru/apps/em-auth/docs#/`
- Kubernetes namespace: `em-auth`

В production используется `ROOT_PATH=/apps/em-auth`, nginx работает как внешний reverse proxy, а деплой выполняется через `GitHub Actions` и манифесты из директории `k3s/`.

Серверный `env` для production хранится в файле:

- `/home/k3s-admin/.prod.env.em-auth`

Локальный шаблон для него: `em-auth.prod.env.example`.

### Что внутри

- Роуты: `fastapi/src/api/v1/*`
- Бизнес-логика: `fastapi/src/services/*`
- Репозитории и работа с БД: `fastapi/src/repositories/*`
- Модели: `fastapi/src/models/*`
- Схемы: `fastapi/src/schemas/*`
- Утилиты (config, auth, db, logger, startup): `fastapi/src/utils/*`
- Middleware и обработчики ошибок: `fastapi/src/middleware/*`, `fastapi/src/exceptions/*`

Детальный backlog и разбор всех реализованных пунктов задания см. в файле `backlog.md`. Декомпозиция требований тестового задания — в `todo.md`.
