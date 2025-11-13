#!/bin/bash

###############################################################################
# ComplyEur Full UI Validation Suite
#
# This script runs a comprehensive UI validation test that:
# - Starts the Flask development server
# - Runs Playwright tests to crawl every page
# - Tests all forms and interactive elements
# - Detects and reports all errors
# - Re-runs tests until all pass
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
QA_DIR="$PROJECT_ROOT/qa/playwright"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ComplyEur Full-Site UI Validation Suite                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to check if Flask is running
check_flask() {
    curl -s http://localhost:5001/health > /dev/null 2>&1
    return $?
}

# Function to start Flask
start_flask() {
    echo -e "${YELLOW}Starting Flask development server...${NC}"
    
    # Kill any existing Flask processes
    pkill -f "python3 run_local.py" 2>/dev/null || true
    sleep 2
    
    # Start Flask in background
    python3 run_local.py > logs/qa_flask.log 2>&1 &
    FLASK_PID=$!
    
    # Wait for Flask to start
    echo "Waiting for Flask to start..."
    for i in {1..30}; do
        if check_flask; then
            echo -e "${GREEN}✓ Flask is running (PID: $FLASK_PID)${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${RED}✗ Flask failed to start${NC}"
    cat logs/qa_flask.log
    return 1
}

# Function to install Playwright if needed
install_playwright() {
    if [ ! -d "$QA_DIR/node_modules" ]; then
        echo -e "${YELLOW}Installing Playwright dependencies...${NC}"
        cd "$QA_DIR"
        npm install --save-dev @playwright/test
        npx playwright install chromium
        cd "$PROJECT_ROOT"
        echo -e "${GREEN}✓ Playwright installed${NC}"
    fi
}

# Function to run Playwright tests
run_tests() {
    echo -e "${BLUE}\n═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Running Playwright Test Suite${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    
    cd "$QA_DIR"
    
    # Run tests
    npx playwright test --config=playwright.config.js --reporter=list,html
    TEST_EXIT_CODE=$?
    
    cd "$PROJECT_ROOT"
    
    return $TEST_EXIT_CODE
}

# Function to analyze results
analyze_results() {
    echo -e "${BLUE}\n═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Analyzing Test Results${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    
    # Check for results files
    if [ -f "$QA_DIR/reports/authenticated-crawl-results.json" ]; then
        echo -e "${GREEN}✓ Authenticated crawl results found${NC}"
        
        # Parse JSON results
        TOTAL_PAGES=$(cat "$QA_DIR/reports/authenticated-crawl-results.json" | grep -o '"totalPages":[0-9]*' | cut -d':' -f2)
        ERRORS=$(cat "$QA_DIR/reports/authenticated-crawl-results.json" | grep -o '"errors":\[' | wc -l)
        
        echo "  Total pages crawled: $TOTAL_PAGES"
        
        if [ -s "$QA_DIR/reports/authenticated-crawl-results.json" ]; then
            # Check for errors in JSON
            if grep -q '"errors":\[\]' "$QA_DIR/reports/authenticated-crawl-results.json"; then
                echo -e "  ${GREEN}✓ No server errors found${NC}"
            else
                echo -e "  ${RED}✗ Server errors detected${NC}"
                echo "  Check: $QA_DIR/reports/authenticated-crawl-results.json"
            fi
        fi
    fi
    
    # Check for HTML report
    if [ -f "$QA_DIR/reports/playwright-report/index.html" ]; then
        echo -e "${GREEN}✓ HTML report generated${NC}"
        echo "  View report: $QA_DIR/reports/playwright-report/index.html"
    fi
    
    # Check for screenshots
    SCREENSHOT_COUNT=$(ls -1 "$QA_DIR/screenshots"/*.png 2>/dev/null | wc -l)
    if [ $SCREENSHOT_COUNT -gt 0 ]; then
        echo -e "${GREEN}✓ $SCREENSHOT_COUNT screenshots captured${NC}"
        echo "  Location: $QA_DIR/screenshots/"
    fi
}

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
    fi
    pkill -f "python3 run_local.py" 2>/dev/null || true
}

# Trap to ensure cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "Project root: $PROJECT_ROOT"
    echo "QA directory: $QA_DIR"
    echo ""
    
    # Check Python and Flask
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found${NC}"
        exit 1
    fi
    
    # Install Playwright if needed
    install_playwright
    
    # Start Flask
    if ! start_flask; then
        echo -e "${RED}✗ Failed to start Flask${NC}"
        exit 1
    fi
    
    # Give Flask a moment to fully initialize
    sleep 3
    
    # Run tests
    MAX_ATTEMPTS=3
    ATTEMPT=1
    
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        echo -e "${BLUE}\n═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}Test Attempt $ATTEMPT of $MAX_ATTEMPTS${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
        
        if run_tests; then
            echo -e "${GREEN}\n✓✓✓ ALL TESTS PASSED ✓✓✓${NC}"
            analyze_results
            exit 0
        else
            echo -e "${YELLOW}\n⚠ Some tests failed${NC}"
            analyze_results
            
            if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
                echo -e "${YELLOW}Retrying in 5 seconds...${NC}"
                sleep 5
            fi
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    echo -e "${RED}\n✗✗✗ TESTS FAILED AFTER $MAX_ATTEMPTS ATTEMPTS ✗✗✗${NC}"
    echo -e "${YELLOW}Check reports and screenshots for details${NC}"
    exit 1
}

# Run main function
main

