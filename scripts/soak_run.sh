#!/usr/bin/env bash
set -euo pipefail
HOURS=${HOURS:-8}
END_AFTER=$((HOURS*60*60))
START=$(date +%s)
i=0
while [ $(( $(date +%s) - START )) -lt $END_AFTER ]; do
  echo "=== SOAK ITERATION $i ($(date)) ==="
  python scripts/make_fixtures.py
  pytest -q tests/backend --maxfail=1 || true
  npx playwright test --config=playwright.config.ts --reporter=line || true
  sleep 5
  ((i++))
done
echo "🕓 Soak complete after $HOURS hours"
