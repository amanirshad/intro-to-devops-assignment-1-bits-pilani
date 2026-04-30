# ACEest Fitness & Gym — CI/CD Implementation Report (Assignment 2)

**Author:** DevOps Engineer, ACEest Fitness & Gym
**Repository:** `bits-pilani-devops-assignment`
**Pipeline:** Git → Jenkins → SonarQube → Docker Hub → Kubernetes (Docker Desktop)

---

## 1. CI/CD Architecture Overview

The pipeline is a single Jenkins declarative pipeline (`Jenkinsfile`) that takes a
commit on `master` from end to running pods on the local Docker Desktop
Kubernetes cluster.

```
┌──────────┐  push   ┌──────────┐   build/test/scan   ┌──────────────┐
│ Developer├────────▶│  GitHub  ├────────────────────▶│   Jenkins    │
└──────────┘  webhook└──────────┘                     └──────┬───────┘
                                                             │
            ┌──────────────────────────┬────────────────────┤
            ▼                          ▼                    ▼
      ┌───────────┐             ┌─────────────┐      ┌──────────────┐
      │ SonarQube │◀── analyse  │ Docker Hub  │      │ K8s (Docker  │
      │ Quality   │             │ aceest-     │◀─pull│  Desktop)    │
      │ Gate      │             │ fitness:tag │      │  ns: aceest  │
      └───────────┘             └─────────────┘      └──────────────┘
```

**Stage flow (Jenkinsfile):**
`Checkout → Setup → Lint → Unit Tests (pytest+coverage) → SonarQube Analysis →
Quality Gate → Docker Build → Docker Push → K8s Deploy (selectable strategy) →
Smoke Test`.

**Local infrastructure** is provisioned through `docker-compose.ci.yml` plus
`scripts/setup-local-ci.sh`:

| Service     | URL                    | Purpose                          |
|-------------|------------------------|----------------------------------|
| Jenkins LTS | http://localhost:8080  | Pipeline orchestration           |
| SonarQube   | http://localhost:9000  | Static analysis & quality gate   |
| Postgres    | internal               | SonarQube storage backend        |
| K8s         | `docker-desktop` ctx   | Deployment target (ns `aceest`)  |

The Jenkins container mounts the host Docker socket (to build/push images) and
the host `~/.kube` directory (to talk to Docker Desktop's K8s control plane).

## 2. Deployment Strategies Implemented

All five strategies required by the brief are version-controlled under `k8s/`,
each exposed on its own `NodePort` for verification:

| Strategy       | Manifest                       | Mechanism                                                          | Rollback                                 |
|----------------|--------------------------------|--------------------------------------------------------------------|------------------------------------------|
| Rolling Update | `k8s/rolling/rolling.yaml`     | `RollingUpdate` strategy, `maxSurge=1`, `maxUnavailable=0`         | `kubectl rollout undo`                   |
| Blue-Green     | `k8s/blue-green/bluegreen.yaml`| Two Deployments + one Service whose `selector.color` is patched   | `switch.sh blue`                         |
| Canary         | `k8s/canary/canary.yaml`       | 4 stable + 1 canary replicas behind a shared label-only Service   | scale canary → 0                         |
| Shadow         | `k8s/shadow/shadow.yaml`       | nginx `mirror` proxy duplicates requests; only primary responds   | delete shadow proxy/deployment           |
| A/B Testing    | `k8s/ab-testing/ab.yaml`       | nginx `map $http_x_variant → upstream` header-based routing       | scale failing variant → 0                |

The pipeline accepts `DEPLOY_STRATEGY` as a build parameter and applies only
the matching folder. The rolling-update path additionally calls
`kubectl rollout status` and triggers an automatic `rollout undo` if the rollout
fails — meeting the "rollback to last stable" requirement.

## 3. Quality Gates and Testing

* **flake8** lints `app.py` with a 120-char limit; pipeline fails on any violation.
* **pytest** runs the suite in `test_app.py`, producing JUnit XML for Jenkins
  and Cobertura coverage XML for SonarQube.
* **SonarQube** consumes both reports via `sonar-project.properties`.
  `sonar.qualitygate.wait=true` plus the `waitForQualityGate` step makes
  the pipeline abort if the project gate is not green — code quality is
  therefore a hard build-breaker, not a soft warning.

## 4. Image Lifecycle and Versioning

Every successful build produces three image tags pushed to Docker Hub:

1. `aceest-fitness:<APP_VERSION>` — semantic, e.g. `v3.2.4`
2. `aceest-fitness:<BUILD_NUMBER>` — Jenkins build id, immutable
3. `aceest-fitness:latest` — convenience pointer

The legacy `code-versions/` files (`Aceestver-1.0` … `3.2.4`) map directly to
these tags so reviewers can trace any image back to its source revision.

## 5. Challenges Faced and Mitigations

| # | Challenge                                                                 | Mitigation                                                                                       |
|---|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| 1 | Apple-Silicon image compatibility for Jenkins/SonarQube                   | Pinned `platform: linux/arm64` in `docker-compose.ci.yml`; used `jenkins:lts-jdk17` ARM image    |
| 2 | Jenkins container needed both Docker and `kubectl` access                 | Mounted `/var/run/docker.sock` and `~/.kube` read-only; installed Kubernetes CLI plugin          |
| 3 | SonarQube quality gate vs fast-feedback Jenkins runs                      | Used `sonar.qualitygate.wait` + `waitForQualityGate` with a 5-minute timeout instead of polling  |
| 4 | Native Kubernetes has no built-in shadow/A-B routing                      | Front-proxied with a tiny nginx Deployment using `mirror` and `map` directives                   |
| 5 | Reliable rollback in rolling updates                                      | Set `revisionHistoryLimit: 5` and chained `rollout status \|\| rollout undo` in the deploy stage |
| 6 | Secrets leaking into `docker push` logs                                   | Used `withCredentials` + `docker login --password-stdin` instead of CLI args                     |

## 6. Key Automation Outcomes

* Single command (`scripts/setup-local-ci.sh`) brings up the entire CI/CD
  control plane on a developer laptop.
* A push to `master` results, with no human intervention, in: lint → tests →
  Sonar gate → multi-tag Docker image on Docker Hub → live pods on
  Docker-Desktop Kubernetes → smoke-test verification.
* Five distinct deployment strategies are selectable from the same
  Jenkins job parameter, exercising the same image artifact.
* Automatic rollback on failed rolling updates and a one-line script for
  blue-green/canary rollback give the team confidence to deploy frequently.
* All infrastructure (`Dockerfile`, `Jenkinsfile`, `docker-compose.ci.yml`,
  `k8s/**`, `sonar-project.properties`) is checked in — the pipeline is fully
  reproducible from the Git history alone.

---

*End of report.*
