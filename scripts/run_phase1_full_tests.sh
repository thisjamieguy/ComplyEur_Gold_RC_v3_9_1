#!/bin/bash
# Phase 1 Stability Lockdown - Full Test Runner
# Runs all test suites 3 consecutive times with server management

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export EUTRACKER_BYPASS_LOGIN=1
export DATABASE_PATH="${DATABASE_PATH:-data/eu_tracker.db}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5001}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASS_COUNT=0
FAIL_COUNT=0
TEST_RESULTS=()

# Function to check if server is running
check_server() {
    curl -s "http://${HOST}:${PORT}/healthz" > /dev/null 2>&1
}

# Function to start server
start_server() {
    if check_server; then
        echo -e "${YELLOW}ℹ️  Server already running on ${HOST}:${PORT}${NC}"
        return 0
    fi
    
    echo "Starting Flask server..."
    EUTRACKER_BYPASS_LOGIN=1 python3 run_local.py > /tmp/complyeur_test_server.log 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    echo "Waiting for server to start..."
    for i in {1..30}; do
        if check_server; then
            echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ Server failed to start${NC}"
    return 1
}

# Function to stop server
stop_server() {
    if [ -n "${SERVER_PID:-}" ]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}

# Function to run Playwright tests
run_playwright_test() {
    local test_file=$1
    local run_number=$2
    
    echo "Running Playwright test: $test_file (Run $run_number/3)"
    
    if npx playwright test "$test_file" --reporter=html,json 2>&1; then
        echo -e "${GREEN}✅ Passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Function to run pytest tests
run_pytest_test() {
    local test_file=$1
    local run_number=$2
    
    echo "Running pytest test: $test_file (Run $run_number/3)"
    
    if python3 -m pytest "$test_file" -v 2>&1; then
        echo -e "${GREEN}✅ Passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Trap to ensure server is stopped on exit
trap stop_server EXIT INT TERM

echo "================================================================================"
echo "Phase 1 Stability Lockdown - Full Test Execution"
echo "================================================================================"
echo ""

# Start server
if ! start_server; then
    echo -e "${RED}❌ Failed to start server${NC}"
    exit 1
fi

# Test suites to run
PLAYWRIGHT_TESTS=(
    "tests/phase1_core_logic.spec.js"
)

PYTEST_TESTS=(
    "tests/db/test_sqlite_wal_consistency.py"
    "tests/db/test_session_manager.py"
)

# Filter existing test files
EXISTING_PLAYWRIGHT_TESTS=()
for test in "${PLAYWRIGHT_TESTS[@]}"; do
    if [ -f "$test" ]; then
        EXISTING_PLAYWRIGHT_TESTS+=("$test")
    else
        echo -e "${YELLOW}⚠️  Test file not found: $test (skipping)${NC}"
    fi
done

EXISTING_PYTEST_TESTS=()
for test in "${PYTEST_TESTS[@]}"; do
    if [ -f "$test" ]; then
        EXISTING_PYTEST_TESTS+=("$test")
    else
        echo -e "${YELLOW}⚠️  Test file not found: $test (skipping)${NC}"
    fi
done

# Run Playwright tests 3 times
for test_suite in "${EXISTING_PLAYWRIGHT_TESTS[@]}"; do
    SUITE_PASSED=0
    for run in 1 2 3; do
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_playwright_test "$test_suite" "$run"; then
            SUITE_PASSED=$((SUITE_PASSED + 1))
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        echo ""
    done
    
    if [ $SUITE_PASSED -eq 3 ]; then
        echo -e "${GREEN}✅ $test_suite: All 3 runs passed${NC}"
        TEST_RESULTS+=("✅ $test_suite: 3/3 passed")
    else
        echo -e "${RED}❌ $test_suite: Only $SUITE_PASSED/3 runs passed${NC}"
        TEST_RESULTS+=("❌ $test_suite: $SUITE_PASSED/3 passed")
    fi
    echo ""
done

# Run pytest tests 3 times
for test_suite in "${EXISTING_PYTEST_TESTS[@]}"; do
    SUITE_PASSED=0
    for run in 1 2 3; do
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_pytest_test "$test_suite" "$run"; then
            SUITE_PASSED=$((SUITE_PASSED + 1))
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        echo ""
    done
    
    if [ $SUITE_PASSED -eq 3 ]; then
        echo -e "${GREEN}✅ $test_suite: All 3 runs passed${NC}"
        TEST_RESULTS+=("✅ $test_suite: 3/3 passed")
    else
        echo -e "${RED}❌ $test_suite: Only $SUITE_PASSED/3 runs passed${NC}"
        TEST_RESULTS+=("❌ $test_suite: $SUITE_PASSED/3 passed")
    fi
    echo ""
done

# Stop server
stop_server

# Summary
echo "================================================================================"
echo "Test Execution Summary"
echo "================================================================================"
echo "Total test runs: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""
echo "Test Results:"
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed 3/3 cycles${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review failures above.${NC}"
    exit 1
fi

