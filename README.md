## Effective Mobile — em-auth-service

Backend-приложение на `FastAPI` и `PostgreSQL` с собственной системой аутентификации и авторизации, построенной поверх `JWT`, `refresh tokens` и таблиц правил доступа в БД.

Продовый Swagger: [https://async-black.ru/apps/em-auth/docs#/](https://async-black.ru/apps/em-auth/docs#/)

### Выполнение задания

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


1. Swagger и API:

### Production (k3s)

- Домен: `async-black.ru`
- Path prefix: `/apps/em-auth`
- Swagger: `https://async-black.ru/apps/em-auth/docs#/`
- Kubernetes namespace: `em-auth`

В production используется `ROOT_PATH=/apps/em-auth`, nginx работает как внешний reverse proxy, а деплой выполняется через `GitHub Actions` и манифесты из директории `k3s/`.

### Таблицы БД

- **users**: учетные записи пользователей (ФИО, email-логин, пароль, метаданные, флаги активности и soft delete).
- **roles**: системные роли (`user`, `manager`, `admin`, `superadmin`).
- **user_roles**: связь many-to-many между пользователями и ролями.
- **resources**: коды ресурсов, к которым применяется авторизация (например, `mock:projects:list`).
- **permissions**: типы действий над ресурсами (например, `read`).
- **access_rules**: правила доступа вида «роль + ресурс + действие → разрешено/запрещено».
- **refresh_tokens**: выданные refresh tokens с возможностью последующего revoke.

### Матрица доступа

#### Пользователи

| Роль        | Кого видит                               | Кого может изменять (`update`)                         | Кого может мягко удалить (`soft delete`)             |
|------------|-------------------------------------------|-------------------------------------------------------|------------------------------------------------------|
| `user`     | Только себя                               | Только себя                                           | Только себя                                          |
| `manager`  | Всех, кроме `admin` и `superadmin`        | Только себя                                           | Только себя                                          |
| `admin`    | Всех                                      | Себя и всех, кроме других `admin` и `superadmin`      | Себя и всех, кроме других `admin` и `superadmin`     |
| `superadmin` | Всех                                   | Всех                                                  | Всех, кроме самого себя                              |

#### Mock-ресурсы

| Роль        | `mock:projects:list` | `mock:reports:list` | `mock:documents:list` |
|------------|----------------------|---------------------|-----------------------|
| `user`     | `read`               | Нет                 | Нет                   |
| `manager`  | `read`               | `read`              | Нет                   |
| `admin`    | `read`               | `read`              | `read`                |
| `superadmin` | `read`             | `read`              | `read`                |

### Что внутри

- Роуты: `fastapi/src/api/v1/*`
- Бизнес-логика: `fastapi/src/services/*`
- Репозитории и работа с БД: `fastapi/src/repositories/*`
- Модели: `fastapi/src/models/*`
- Схемы: `fastapi/src/schemas/*`
- Утилиты (config, auth, db, logger, startup): `fastapi/src/utils/*`
- Middleware и обработчики ошибок: `fastapi/src/middleware/*`, `fastapi/src/exceptions/*`


