#!/usr/bin/env bash
set -euo pipefail

ACTIVE_CI_PROVIDER_EXPECTED="${ACTIVE_CI_PROVIDER_EXPECTED:-github}"
SERVER_ENV_PATH="${SERVER_ENV_PATH:-/home/${K3S_SSH_USER}/.prod.env.em-auth}"

if [[ -z "${K3S_SSH_KEY_PATH:-}" || -z "${K3S_SSH_USER:-}" || -z "${K3S_SERVER_IP:-}" ]]; then
  echo "⚠️  check-active-provider: K3S_SSH_KEY_PATH, K3S_SSH_USER или K3S_SERVER_IP не заданы, пропускаем проверку"
  exit 0
fi

TMP_ENV="/tmp/prod.env"

if ssh -i "$K3S_SSH_KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=10 \
    -o BatchMode=yes \
    "${K3S_SSH_USER}@${K3S_SERVER_IP}" "test -f ${SERVER_ENV_PATH} && cat ${SERVER_ENV_PATH}" > "$TMP_ENV" 2>/dev/null; then
  ACTIVE_CI_PROVIDER=$(grep "^ACTIVE_CI_PROVIDER=" "$TMP_ENV" 2>/dev/null | sed 's/ACTIVE_CI_PROVIDER=//g' || echo "")
  rm -f "$TMP_ENV"
else
  echo "⚠️  check-active-provider: не удалось прочитать ${SERVER_ENV_PATH} на сервере, пропускаем проверку"
  exit 0
fi

if [[ -z "$ACTIVE_CI_PROVIDER" ]]; then
  echo "⚠️  ACTIVE_CI_PROVIDER не задан в ${SERVER_ENV_PATH}, деплой разрешён для любого CI"
  exit 0
fi

echo "ℹ️  ACTIVE_CI_PROVIDER=${ACTIVE_CI_PROVIDER}, ожидается: ${ACTIVE_CI_PROVIDER_EXPECTED}"

if [[ "$ACTIVE_CI_PROVIDER" != "$ACTIVE_CI_PROVIDER_EXPECTED" ]]; then
  echo "⚠️  Текущий CI (${ACTIVE_CI_PROVIDER_EXPECTED}) не активен по ACTIVE_CI_PROVIDER, деплой пропускаем"
  exit 1
fi

echo "✅ ACTIVE_CI_PROVIDER совпадает, деплой разрешён"
