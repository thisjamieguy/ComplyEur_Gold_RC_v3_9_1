#!/bin/bash
# Elite QA Task Force - Main Execution Script
# Runs comprehensive test suite with iterative validation loops

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🔬 ELITE QA TASK FORCE - COMPLYEUR COMPREHENSIVE TESTING"
echo "============================================================"
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Start Time: $(date)"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Ensure test directory exists
mkdir -p tests/qa_elite
mkdir -p reports/qa_elite

# Run the iterative test runner
echo "============================================================"
echo "Running Iterative Test Suite..."
echo "============================================================"
echo ""

python3 -m pytest tests/qa_elite/test_runner.py -v --tb=short || python3 tests/qa_elite/test_runner.py

# Generate certification report if test results exist
if [ -f "reports/qa_elite/qa_report_*.json" ]; then
    echo ""
    echo "============================================================"
    echo "Generating Certification Report..."
    echo "============================================================"
    echo ""
    
    LATEST_JSON=$(ls -t reports/qa_elite/qa_report_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_JSON" ]; then
        python3 -c "
from tests.qa_elite.certification_report import generate_certification_from_results
import sys
report_path = generate_certification_from_results('$LATEST_JSON')
print(f'Certification report: {report_path}')
"
    fi
fi

echo ""
echo "============================================================"
echo "✅ ELITE QA TASK FORCE EXECUTION COMPLETE"
echo "============================================================"
echo "End Time: $(date)"
echo ""
echo "Reports available in: reports/qa_elite/"
echo ""




