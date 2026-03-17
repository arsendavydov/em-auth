## CI папка

Эта папка предназначена для всего, что относится к CI/CD в проекте `em-auth`.

Планируемая структура по аналогии с `Shum`:

- `ci/` — общие скрипты для деплоя
  - `get-kubeconfig.sh`
  - `create-configmap-and-secret.sh`
  - `apply-manifests.sh`
  - `helpers.sh`
- `ci/common/` — общие проверки и вспомогательные утилиты
  - `check-active-provider.sh`
- `ci/github/` — документация и GitHub-специфичные заметки

Почему структура создается заранее:

- чтобы разнести reusable shell-скрипты и workflow-конфигурацию;
- чтобы повторить понятную схему из `Shum`;
- чтобы не смешивать логику GitHub Actions и bash-скрипты деплоя в одном файле.

Важно:

- для `em-auth` используется отдельный server-side env-файл:
  - `/home/k3s-admin/.prod.env.em-auth`
- это нужно, чтобы не пересекаться по переменным с `Shum`.

Что будет добавлено следующим шагом:

- скрипты для получения `kubeconfig` с сервера;
- создание `ConfigMap` / `Secret` из `.prod.env`;
- применение `k3s` манифестов;
- проверка активного CI провайдера;
- интеграция с `.github/workflows/deploy.yml`.
