#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup-local-ci.sh
# One-shot bootstrap for the local Jenkins + SonarQube + Kubernetes stack on
# macOS (Apple Silicon). Idempotent - safe to re-run.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

log() { printf "\033[1;36m[setup]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; }

# ── Pre-flight checks ────────────────────────────────────────────────────────
command -v docker  >/dev/null 2>&1 || { err "Docker is not installed"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { err "kubectl is not installed"; exit 1; }

if ! docker info >/dev/null 2>&1; then
  err "Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

log "Verifying Docker Desktop Kubernetes context…"
if ! kubectl config get-contexts docker-desktop >/dev/null 2>&1; then
  err "Kubernetes is not enabled in Docker Desktop. Enable it under Settings → Kubernetes."
  exit 1
fi
kubectl config use-context docker-desktop >/dev/null
kubectl cluster-info >/dev/null

# ── Bring up Jenkins + SonarQube ─────────────────────────────────────────────
log "Starting Jenkins + SonarQube stack…"
docker compose -f docker-compose.ci.yml up -d

log "Waiting for Jenkins to become ready…"
for _ in {1..60}; do
  if curl -fsS http://localhost:8080/login >/dev/null 2>&1; then
    log "Jenkins is up at http://localhost:8080"
    break
  fi
  sleep 5
done

log "Initial Jenkins admin password:"
docker exec aceest-jenkins cat /var/jenkins_home/secrets/initialAdminPassword || true

log "Waiting for SonarQube to become ready (this can take ~1 min)…"
for _ in {1..60}; do
  if curl -fsS http://localhost:9000/api/system/status | grep -q '"status":"UP"'; then
    log "SonarQube is up at http://localhost:9000  (default creds: admin / admin)"
    break
  fi
  sleep 5
done

# ── Apply application namespace ──────────────────────────────────────────────
log "Creating Kubernetes namespace 'aceest'…"
kubectl apply -f k8s/base/namespace.yaml

cat <<'EOF'

───────────────────────────────────────────────────────────────────────────────
  Local CI/CD stack is ready.

  Next manual steps (one-time):
    1. Open Jenkins   → http://localhost:8080  (use the admin password printed above)
       - Install suggested plugins
       - Add plugins: Docker Pipeline, SonarQube Scanner, Kubernetes CLI, Pipeline Utility Steps
       - Configure tool: SonarQube Scanner (auto-install)
       - Configure system → SonarQube servers → name: 'sonar', URL: http://sonarqube:9000, token credential
       - Add credentials:
           dockerhub-creds (username + access token)
           sonar-token     (SonarQube user token, secret text)
           kubeconfig      (~/.kube/config, secret file)
       - Create new Pipeline job 'aceest-fitness' pointing at this Git repo, script path = Jenkinsfile

    2. Open SonarQube → http://localhost:9000
       - Reset admin password
       - Create project key 'aceest-fitness'  → generate a token → store as Jenkins credential 'sonar-token'

    3. Trigger the pipeline (Build Now or push a commit).
───────────────────────────────────────────────────────────────────────────────
EOF
