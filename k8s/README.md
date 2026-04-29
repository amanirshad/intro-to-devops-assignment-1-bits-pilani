# Kubernetes Manifests — ACEest Fitness & Gym

This directory implements all five deployment strategies required by Assignment 2.
Every manifest uses placeholder `DOCKERHUB_USER` and (where versioned) `IMAGE_TAG`
which the Jenkins pipeline (or the helper script below) substitutes at deploy time.

| Strategy        | Folder              | NodePort | Quick test |
|-----------------|---------------------|----------|------------|
| Default / Base  | `base/`             | 30080    | `curl localhost:30080` |
| Rolling Update  | `rolling/`          | 30083    | `kubectl rollout status deploy/aceest-rolling -n aceest` |
| Blue-Green      | `blue-green/`       | 30081    | `./blue-green/switch.sh green` |
| Canary          | `canary/`           | 30082    | `for i in {1..20}; do curl -s localhost:30082; done` |
| Shadow          | `shadow/`           | 30084    | mirrors traffic to v3.2.4 silently |
| A/B Testing     | `ab-testing/`       | 30085    | `curl -H "X-Variant: B" localhost:30085` |

## Apply everything

```bash
DOCKERHUB_USER=<your-dockerhub-user>
IMAGE_TAG=v3.2.4

kubectl apply -f base/namespace.yaml

for f in $(find . -name '*.yaml' ! -name 'namespace.yaml'); do
  sed -e "s|DOCKERHUB_USER|${DOCKERHUB_USER}|g" \
      -e "s|IMAGE_TAG|${IMAGE_TAG}|g" "$f" | kubectl apply -f -
done
```

## Rollback cheatsheet

| Strategy   | Rollback command |
|------------|------------------|
| Rolling    | `kubectl -n aceest rollout undo deploy/aceest-rolling` |
| Blue-Green | `./blue-green/switch.sh blue` |
| Canary     | `kubectl -n aceest scale deploy/aceest-canary --replicas=0` |
| Shadow     | n/a — shadow never serves users |
| A/B        | scale failing variant to 0 |
