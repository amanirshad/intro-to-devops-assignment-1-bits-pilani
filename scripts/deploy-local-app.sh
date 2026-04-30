#!/usr/bin/env bash
# Deploy ACEest Fitness to the local Docker Desktop Kubernetes cluster.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

log() { printf '\033[1;36m[deploy]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

DOCKERHUB_USER="${1:-aceestdevops}"
IMAGE_TAG="${2:-v3.2.4}"
STRATEGY="${3:-base}"
IMAGE_NAME="${DOCKERHUB_USER}/aceest-fitness:${IMAGE_TAG}"

command -v docker >/dev/null 2>&1 || { err "Docker is not installed"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { err "kubectl is not installed"; exit 1; }

docker info >/dev/null 2>&1 || { err "Docker daemon is not running"; exit 1; }
kubectl config current-context >/dev/null 2>&1 || { err "kubectl is not configured"; exit 1; }

case "${STRATEGY}" in
  base|rolling|blue-green|canary|shadow|ab-testing)
    ;;
  *)
    err "Unknown strategy: ${STRATEGY}"
    exit 1
    ;;
esac

log "Building image ${IMAGE_NAME}…"
docker build -t "${IMAGE_NAME}" .

log "Ensuring namespace aceest exists…"
kubectl apply -f k8s/base/namespace.yaml >/dev/null

strategy_dir="k8s/${STRATEGY}"
log "Applying manifests from ${strategy_dir}…"
while IFS= read -r manifest; do
  [ -n "${manifest}" ] || continue
  sed -e "s|DOCKERHUB_USER|${DOCKERHUB_USER}|g" \
      -e "s|IMAGE_TAG|${IMAGE_TAG}|g" "${manifest}" | kubectl apply -n aceest -f -
done < <(find "${strategy_dir}" -name '*.yaml' | sort)

case "${STRATEGY}" in
  base)
    kubectl -n aceest rollout status deploy/aceest-fitness --timeout=180s
    log "App is available at http://localhost:30080"
    ;;
  rolling)
    kubectl -n aceest rollout status deploy/aceest-rolling --timeout=180s
    log "App is available at http://localhost:30083"
    ;;
  blue-green)
    log "Use k8s/blue-green/switch.sh to move traffic between blue and green"
    log "Service is exposed on http://localhost:30081"
    ;;
  canary)
    log "App is available at http://localhost:30082"
    ;;
  shadow)
    log "App is available at http://localhost:30084"
    ;;
  ab-testing)
    log "App is available at http://localhost:30085"
    ;;
esac
