## Workflows

Каталог зарезервирован под `GitHub Actions` workflow-файлы.

Следующим шагом сюда будет добавлен `deploy.yml` для:

- unit-тестов и проверок;
- сборки образов `fastapi` и `nginx`;
- деплоя в `k3s`;
- проверки доступности `https://async-black.ru/apps/em-auth/docs#/`.

Пока активный workflow не добавлен намеренно, чтобы не запускать незавершенный CD pipeline до готовности:

- `k3s` манифестов;
- shell-скриптов из `ci/`;
- production secrets и server-side `.prod.env`.
