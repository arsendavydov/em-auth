#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/helpers.sh"

: "${KUBE_NAMESPACE:?KUBE_NAMESPACE is required}"
SERVER_ENV_PATH="${SERVER_ENV_PATH:-/home/${K3S_SSH_USER}/.prod.env.em-auth}"

TMP_ENV="/tmp/prod.env"
TMP_ENV_CLEAN="/tmp/prod.env.clean"

echo "📥 Загрузка переменных из ${SERVER_ENV_PATH} на сервере..."
if ssh -i "$K3S_SSH_KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=10 \
    -o BatchMode=yes \
    "$K3S_SSH_HOST" "test -f ${SERVER_ENV_PATH} && cat ${SERVER_ENV_PATH}" > "$TMP_ENV" 2>/dev/null; then
  echo "✅ Файл ${SERVER_ENV_PATH} найден"
  grep -v '^#' "$TMP_ENV" | grep -v '^$' | grep '=' > "$TMP_ENV_CLEAN" 2>/dev/null || true
  if [[ -s "$TMP_ENV_CLEAN" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$TMP_ENV_CLEAN" 2>/dev/null || true
    set +a
  fi
  rm -f "$TMP_ENV" "$TMP_ENV_CLEAN"
else
  echo "⚠️  ${SERVER_ENV_PATH} не найден на сервере, используем только переменные из CI"
fi

: "${PROJECT_NAME:=em-auth-service}"
: "${ENVIRONMENT:=production}"
: "${API_HOST:=0.0.0.0}"
: "${API_PORT:=8000}"
: "${ROOT_PATH:=/apps/em-auth}"
: "${POSTGRES_HOST:=postgres-service}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=auth_db}"
: "${ACCESS_TOKEN_EXPIRE_MINUTES:=30}"
: "${REFRESH_TOKEN_EXPIRE_DAYS:=7}"
: "${JWT_ALGORITHM:=HS256}"
: "${LOG_LEVEL:=info}"
: "${RATE_LIMIT_PER_MINUTE:=60}"
: "${RATE_LIMIT_AUTH_PER_MINUTE:=5}"

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${SECRET_KEY:?SECRET_KEY is required}"

ensure_tunnel

# Убедимся, что namespace для em-auth существует перед созданием ConfigMap/Secret
kubectl get namespace "$KUBE_NAMESPACE" --request-timeout=30s >/dev/null 2>&1 || \
  kubectl create namespace "$KUBE_NAMESPACE" --request-timeout=30s

kubectl delete configmap em-auth-config -n "$KUBE_NAMESPACE" --ignore-not-found=true --request-timeout=30s || true
kubectl create configmap em-auth-config \
  --from-literal=PROJECT_NAME="$PROJECT_NAME" \
  --from-literal=ENVIRONMENT="$ENVIRONMENT" \
  --from-literal=API_HOST="$API_HOST" \
  --from-literal=API_PORT="$API_PORT" \
  --from-literal=ROOT_PATH="$ROOT_PATH" \
  --from-literal=POSTGRES_HOST="$POSTGRES_HOST" \
  --from-literal=POSTGRES_PORT="$POSTGRES_PORT" \
  --from-literal=POSTGRES_DB="$POSTGRES_DB" \
  --from-literal=ACCESS_TOKEN_EXPIRE_MINUTES="$ACCESS_TOKEN_EXPIRE_MINUTES" \
  --from-literal=REFRESH_TOKEN_EXPIRE_DAYS="$REFRESH_TOKEN_EXPIRE_DAYS" \
  --from-literal=JWT_ALGORITHM="$JWT_ALGORITHM" \
  --from-literal=LOG_LEVEL="$LOG_LEVEL" \
  --from-literal=RATE_LIMIT_PER_MINUTE="$RATE_LIMIT_PER_MINUTE" \
  --from-literal=RATE_LIMIT_AUTH_PER_MINUTE="$RATE_LIMIT_AUTH_PER_MINUTE" \
  --namespace="$KUBE_NAMESPACE" \
  --request-timeout=30s
echo "✅ ConfigMap em-auth-config создан/обновлен"

kubectl delete secret em-auth-secrets -n "$KUBE_NAMESPACE" --ignore-not-found=true --request-timeout=30s || true
kubectl create secret generic em-auth-secrets \
  --from-literal=POSTGRES_USER="$POSTGRES_USER" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --namespace="$KUBE_NAMESPACE" \
  --request-timeout=30s
echo "✅ Secret em-auth-secrets создан/обновлен"

if [[ -n "${CI_REGISTRY:-}" ]]; then
  if [[ "$CI_REGISTRY" == *"ghcr.io"* ]] || [[ "${CI_REGISTRY_IMAGE:-}" == *"ghcr.io"* ]]; then
    REGISTRY_SERVER="ghcr.io"
    SECRET_NAME="ghcr-registry-secret"
  elif [[ "$CI_REGISTRY" == *"registry.gitlab.com"* ]] || [[ "${CI_REGISTRY_IMAGE:-}" == *"registry.gitlab.com"* ]]; then
    REGISTRY_SERVER="registry.gitlab.com"
    SECRET_NAME="gitlab-registry-secret"
  else
    REGISTRY_SERVER="${CI_REGISTRY}"
    SECRET_NAME="registry-secret"
  fi
else
  REGISTRY_SERVER="ghcr.io"
  SECRET_NAME="ghcr-registry-secret"
fi

if [[ -n "${CI_REGISTRY_USER:-}" && -n "${CI_REGISTRY_PASSWORD:-}" ]]; then
  kubectl delete secret "$SECRET_NAME" -n "$KUBE_NAMESPACE" --ignore-not-found=true --request-timeout=30s || true
  kubectl create secret docker-registry "$SECRET_NAME" \
    --docker-server="$REGISTRY_SERVER" \
    --docker-username="$CI_REGISTRY_USER" \
    --docker-password="$CI_REGISTRY_PASSWORD" \
    --docker-email="${CI_REGISTRY_EMAIL:-noreply@example.com}" \
    --namespace="$KUBE_NAMESPACE" \
    --request-timeout=30s
  echo "✅ imagePullSecret $SECRET_NAME создан/обновлен"
else
  echo "⚠️  CI_REGISTRY_USER/CI_REGISTRY_PASSWORD не заданы, imagePullSecret не обновлялся"
fi
