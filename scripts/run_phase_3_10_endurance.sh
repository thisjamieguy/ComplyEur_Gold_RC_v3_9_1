#!/bin/bash
# ===============================================================
# Phase 3.10: Elite QA Endurance & Stress Testing
# ===============================================================
# Runs 180-minute continuous stress test of ComplyEur's
# calculation engine, backend integrity, and frontend synchronization.
# ===============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🌙 PHASE 3.10: ELITE QA ENDURANCE & STRESS TESTING"
echo "============================================================"
echo "Project Root: $PROJECT_ROOT"
echo "Start Time: $(date)"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Ensure admin login bypass for automated Playwright sessions
export EUTRACKER_BYPASS_LOGIN=${EUTRACKER_BYPASS_LOGIN:-1}

# Check if Flask app is running
APP_URL="${APP_URL:-http://127.0.0.1:5001}"
if ! curl -s "${APP_URL}/healthz" > /dev/null 2>&1; then
    echo "⚠️  Flask app is not running on ${APP_URL}"
    echo "    Starting server in background..."
    python run_local.py > /tmp/complyeur_endurance_server.log 2>&1 &
    SERVER_PID=$!
    echo "    Server starting (PID: $SERVER_PID)..."
    echo "    Waiting up to 30 seconds for server to be ready..."
    
    for i in {1..30}; do
        if curl -s "${APP_URL}/healthz" > /dev/null 2>&1; then
            echo "    ✅ Server is ready!"
            break
        fi
        sleep 1
    done
    
    if ! curl -s "${APP_URL}/healthz" > /dev/null 2>&1; then
        echo "    ❌ Server failed to start. Check /tmp/complyeur_endurance_server.log"
        echo "    Please start the server manually: python run_local.py"
        exit 1
    fi
else
    echo "✅ Flask app is running"
fi

# Ensure report directories exist
mkdir -p reports/qa_elite/endurance

# Set test duration (default: 180 minutes / 3 hours)
TEST_DURATION_MINUTES="${TEST_DURATION_MINUTES:-180}"
export TEST_DURATION_MINUTES

echo ""
echo "============================================================"
echo "Running Endurance Test Suite..."
echo "Duration: ${TEST_DURATION_MINUTES} minutes"
echo "============================================================"
echo ""

# Run the endurance test
python3 -m pytest tests/qa_elite/phase_3_10_endurance_stress.py -v -s --tb=short || \
python3 tests/qa_elite/phase_3_10_endurance_stress.py \
    --db-path "${DATABASE_PATH:-data/eu_tracker.db}" \
    --app-url "${APP_URL}" \
    --admin-password "${ADMIN_PASSWORD:-admin123}" \
    --duration "${TEST_DURATION_MINUTES}"

echo ""
echo "============================================================"
echo "✅ PHASE 3.10 ENDURANCE TEST COMPLETE"
echo "============================================================"
echo "End Time: $(date)"
echo ""
echo "Reports available in: reports/qa_elite/endurance/"
echo ""

# Cleanup server if we started it
if [ -n "$SERVER_PID" ]; then
    echo "Stopping test server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
fi

