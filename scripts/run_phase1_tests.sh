#!/bin/bash
# Phase 1 Stability Lockdown - Test Runner
# Runs all test suites 3 consecutive times

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export EUTRACKER_BYPASS_LOGIN=1
export DATABASE_PATH="${DATABASE_PATH:-data/eu_tracker.db}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "Phase 1 Stability Lockdown - Test Execution"
echo "================================================================================"
echo ""

# Test suites to run
TEST_SUITES=(
    "tests/phase1_core_logic.spec.js"
)

# Additional test files if they exist
if [ -f "tests/test_db_integrity.py" ]; then
    TEST_SUITES+=("tests/test_db_integrity.py")
fi

if [ -f "tests/db/test_sqlite_wal_consistency.py" ]; then
    TEST_SUITES+=("tests/db/test_sqlite_wal_consistency.py")
fi

if [ -f "tests/db/test_session_manager.py" ]; then
    TEST_SUITES+=("tests/db/test_session_manager.py")
fi

# Function to run a test suite
run_test_suite() {
    local test_file=$1
    local run_number=$2
    local total_runs=$3
    
    echo "--------------------------------------------------------------------------------"
    echo "Running: $test_file (Run $run_number/$total_runs)"
    echo "--------------------------------------------------------------------------------"
    
    if [[ "$test_file" == *.spec.js ]] || [[ "$test_file" == *.spec.ts ]]; then
        # Playwright test
        if npx playwright test "$test_file" --reporter=html,json 2>&1; then
            echo -e "${GREEN}✅ Passed${NC}"
            return 0
        else
            echo -e "${RED}❌ Failed${NC}"
            return 1
        fi
    elif [[ "$test_file" == *.py ]]; then
        # pytest
        if python -m pytest "$test_file" -v 2>&1; then
            echo -e "${GREEN}✅ Passed${NC}"
            return 0
        else
            echo -e "${RED}❌ Failed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Unknown test file type: $test_file${NC}"
        return 1
    fi
}

# Run each test suite 3 times
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=0

for test_suite in "${TEST_SUITES[@]}"; do
    if [ ! -f "$test_suite" ]; then
        echo -e "${YELLOW}⚠️  Test file not found: $test_suite (skipping)${NC}"
        continue
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 3))
    SUITE_PASSED=0
    
    for run in 1 2 3; do
        if run_test_suite "$test_suite" "$run" 3; then
            SUITE_PASSED=$((SUITE_PASSED + 1))
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        echo ""
    done
    
    if [ $SUITE_PASSED -eq 3 ]; then
        echo -e "${GREEN}✅ $test_suite: All 3 runs passed${NC}"
    else
        echo -e "${RED}❌ $test_suite: Only $SUITE_PASSED/3 runs passed${NC}"
    fi
    echo ""
done

# Summary
echo "================================================================================"
echo "Test Execution Summary"
echo "================================================================================"
echo "Total test runs: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed 3/3 cycles${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review failures above.${NC}"
    exit 1
fi

