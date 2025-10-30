#!/usr/bin/env bash

# Automated EU Trip Tracker calendar QA harness
# -------------------------------------------------
# This script spins up the Flask calendar server on localhost:5001,
# runs the Playwright QA suite, and then opens the HTML report.
#
# Usage:
#   tools/run_calendar_qa.sh
#
# Optional environment overrides:
#   PYTHON         - Python interpreter to use (defaults to ./venv/bin/python)
#   HOST           - Host interface for the Flask app (defaults to 127.0.0.1)
#   PORT           - Port for the Flask app (defaults to 5001)
#   CALENDAR_QA_USE_FIXTURES
#                   - Set to 0 to run against live backend responses instead of fixtures

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/tools"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5001}"
CALENDAR_URL="http://$HOST:$PORT/calendar"

DEFAULT_PYTHON="$ROOT_DIR/venv/bin/python"
PYTHON_BIN="${PYTHON:-$DEFAULT_PYTHON}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "[QA] Python interpreter not found at '$PYTHON_BIN'." >&2
  echo "[QA] Provide PYTHON env var or set up the project virtualenv." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[QA] npm is required but not installed or not on PATH." >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "[QA] npx is required but not installed or not on PATH." >&2
  exit 1
fi

log() {
  printf '[QA] %s\n' "$*"
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    log "Stopping Flask server (pid $SERVER_PID)"
    if ps -p "$SERVER_PID" >/dev/null 2>&1; then
      kill "$SERVER_PID" >/dev/null 2>&1 || true
      wait "$SERVER_PID" 2>/dev/null || true
    fi
  fi
}

trap cleanup EXIT INT TERM

log "Project root: $ROOT_DIR"
cd "$ROOT_DIR"

log "Ensuring Playwright browsers are installed"
npx playwright install >/dev/null

log "Starting Flask server on $HOST:$PORT (background)"
FLASK_DEBUG=${FLASK_DEBUG:-false} HOST="$HOST" PORT="$PORT" "$PYTHON_BIN" "$ROOT_DIR/run_local.py" >/tmp/calendar_qa_server.log 2>&1 &
SERVER_PID=$!

log "Waiting for server readiness at $CALENDAR_URL"
READY=false
for attempt in {1..30}; do
  if curl --fail --silent --output /dev/null "$CALENDAR_URL"; then
    READY=true
    break
  fi
  sleep 1
done

if [[ "$READY" != true ]]; then
  log "Server failed to start after 30 seconds. Check /tmp/calendar_qa_server.log for details." >&2
  exit 1
fi

log "Server is up. Running Playwright QA suite"
npm run test:qa

log "QA suite complete. Opening HTML report"
npx playwright show-report

log "QA automation finished successfully"

