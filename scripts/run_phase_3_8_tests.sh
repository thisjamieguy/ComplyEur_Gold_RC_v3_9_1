#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${ROOT_DIR}/tests/tmp"
REPORT_DIR="${ROOT_DIR}/reports"
FIXTURE_DB="${ROOT_DIR}/tests/fixtures/test_data.db"

mkdir -p "${TMP_DIR}"
mkdir -p "${REPORT_DIR}"

TEMP_DB="$(mktemp "${TMP_DIR}/phase38_db.XXXXXX.sqlite")"
cp "${FIXTURE_DB}" "${TEMP_DB}"

export DATABASE_PATH="${TEMP_DB}"
export SQLALCHEMY_DATABASE_URI="sqlite:///${TEMP_DB}"
export AUTH_TOTP_ENABLED="false"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5001}"
export FLASK_DEBUG="0"
export PYTHONUNBUFFERED="1"
export PLAYWRIGHT_JUNIT_OUTPUT="${ROOT_DIR}/playwright-report/results.xml"

if [ -f "${ROOT_DIR}/venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/venv/bin/activate"
fi

SERVER_LOG="$(mktemp "${TMP_DIR}/phase38_server.XXXXXX.log")"
PYTEST_LOG="$(mktemp "${TMP_DIR}/phase38_pytest.XXXXXX.log")"
PLAYWRIGHT_LOG="$(mktemp "${TMP_DIR}/phase38_playwright.XXXXXX.log")"

cleanup() {
  local exit_code=$?
  if [ -n "${SERVER_PID:-}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  rm -f "${TEMP_DB}" "${SERVER_LOG}" "${PYTEST_LOG}" "${PLAYWRIGHT_LOG}"
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

pushd "${ROOT_DIR}" >/dev/null || exit 1
python3 run_local.py >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!
popd >/dev/null || exit 1

# Wait for health endpoint
if ! python3 - <<'PY'
import os
import time
import urllib.error
import urllib.request

host = os.environ.get("HOST", "127.0.0.1")
port = os.environ.get("PORT", "5001")
url = f"http://{host}:{port}/healthz"

for attempt in range(60):
    try:
        with urllib.request.urlopen(url, timeout=1):
            raise SystemExit(0)
    except urllib.error.URLError:
        time.sleep(1)
raise SystemExit("Server failed to respond to /healthz within 60 seconds")
PY
then
  echo "Server failed to respond to /healthz within 60 seconds" >&2
  exit 1
fi

pushd "${ROOT_DIR}" >/dev/null || exit 1
pytest tests/test_login.py tests/test_trip_update_api.py tests/test_db_integrity.py --maxfail=1 --disable-warnings | tee "${PYTEST_LOG}"
PYTEST_EXIT=${PIPESTATUS[0]}
popd >/dev/null || exit 1

pushd "${ROOT_DIR}" >/dev/null || exit 1
npx playwright test tests/test_calendar_ui.spec.ts --reporter=line | tee "${PLAYWRIGHT_LOG}"
PLAYWRIGHT_EXIT=${PIPESTATUS[0]}
popd >/dev/null || exit 1

OVERALL_EXIT=$(( PYTEST_EXIT | PLAYWRIGHT_EXIT ))

export REPORT_FILE="${REPORT_DIR}/test_report.html"
export PYTEST_LOG
export PLAYWRIGHT_LOG
export PYTEST_EXIT
export PLAYWRIGHT_EXIT

python3 - <<'PY'
import html
import os
from datetime import datetime

report_path = os.environ["REPORT_FILE"]
pytest_log_path = os.environ["PYTEST_LOG"]
playwright_log_path = os.environ["PLAYWRIGHT_LOG"]
pytest_exit = int(os.environ["PYTEST_EXIT"])
playwright_exit = int(os.environ["PLAYWRIGHT_EXIT"])

def read_log(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return ""

pytest_log = html.escape(read_log(pytest_log_path))
playwright_log = html.escape(read_log(playwright_log_path))

status_row = lambda name, code: f"<li><strong>{name}</strong>: {'Passed' if code == 0 else 'Failed'} (exit {code})</li>"

report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ComplyEur Calendar Phase 3.8 Test Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; background: #f8fafc; }}
    h1 {{ color: #0f172a; }}
    pre {{ background: #0f172a; color: #e2e8f0; padding: 1rem; overflow-x: auto; border-radius: 6px; }}
    section {{ margin-bottom: 2rem; }}
    ul {{ list-style: disc; padding-left: 1.5rem; }}
  </style>
</head>
<body>
  <h1>ComplyEur Calendar Phase 3.8 Test Report</h1>
  <p>Generated: {datetime.utcnow().isoformat()}Z</p>
  <section>
    <h2>Summary</h2>
    <ul>
      {status_row("Pytest backend suite", pytest_exit)}
      {status_row("Playwright UI suite", playwright_exit)}
    </ul>
  </section>
  <section>
    <h2>Pytest Output</h2>
    <pre>{pytest_log or 'No output captured.'}</pre>
  </section>
  <section>
    <h2>Playwright Output</h2>
    <pre>{playwright_log or 'No output captured.'}</pre>
  </section>
</body>
</html>"""

with open(report_path, "w", encoding="utf-8") as handle:
    handle.write(report_html)
PY

if [ "${OVERALL_EXIT}" -ne 0 ]; then
  exit "${OVERALL_EXIT}"
fi
