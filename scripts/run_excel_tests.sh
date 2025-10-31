#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PLAYWRIGHT_DB_PATH="${ROOT_DIR}/tests/tmp/playwright_e2e.db"

mkdir -p "${ROOT_DIR}/tests/tmp"
rm -f "${PLAYWRIGHT_DB_PATH}"

pushd "${ROOT_DIR}" >/dev/null
npx playwright test tests/excel_import/*.spec.js --workers=1 "$@"
popd >/dev/null
