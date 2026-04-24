#!/usr/bin/env bash
# Tear down the local Jenkins + SonarQube stack and remove the K8s namespace.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

docker compose -f docker-compose.ci.yml down
kubectl delete namespace aceest --ignore-not-found
echo "[teardown] Local CI/CD stack removed."
