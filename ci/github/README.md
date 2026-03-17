## GitHub CI/CD notes

Здесь будет документация и вспомогательные заметки для `GitHub Actions`.

План:

- workflow в `.github/workflows/deploy.yml`;
- использование `GitHub Secrets` для:
  - `K3S_SERVER_IP`
  - `K3S_SSH_USER`
  - `K3S_SSH_KEY_BASE64`
  - `CI_REGISTRY`
  - `CI_REGISTRY_USER`
  - `CI_REGISTRY_PASSWORD`
  - `CI_REGISTRY_IMAGE`
  - `DOMAIN`
- вызов общих скриптов из `ci/`, а не хранение всей deploy-логики прямо в workflow.
- server-side env для этого проекта хранится отдельно:
  - `/home/k3s-admin/.prod.env.em-auth`
