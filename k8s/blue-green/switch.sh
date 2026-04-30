#!/usr/bin/env bash
# Cut traffic to the other colour, then optionally rollback.
# Usage: ./switch.sh green    | ./switch.sh blue
set -euo pipefail
COLOR="${1:-green}"
[[ "$COLOR" == "blue" || "$COLOR" == "green" ]] || { echo "color must be blue|green"; exit 1; }
kubectl -n aceest patch service aceest-bluegreen \
  -p "{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"color\":\"${COLOR}\"}}}"
echo "[blue-green] traffic switched to ${COLOR}"
