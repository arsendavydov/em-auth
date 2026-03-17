#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/helpers.sh"

: "${KUBE_NAMESPACE:?KUBE_NAMESPACE is required}"

echo "🔧 Применение Kubernetes манифестов для em-auth..."

ensure_tunnel

apply_with_retry k3s/namespace.yaml
apply_with_retry k3s/postgres-statefulset.yaml
apply_with_retry k3s/nginx-configmap.yaml
apply_with_retry k3s/fastapi-service.yaml
apply_with_retry k3s/fastapi-deployment.yaml
apply_with_retry k3s/nginx-service.yaml
apply_with_retry k3s/nginx-deployment.yaml
apply_with_retry k3s/ingress.yaml

echo "📊 Текущий статус подов:"
kubectl get pods -n "$KUBE_NAMESPACE" || true

echo "✅ Манифесты em-auth применены"
