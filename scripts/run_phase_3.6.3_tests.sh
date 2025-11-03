#!/bin/bash

# ==========================================================
#  EU 90/180 Employee Travel Tracker
#  Phase 3.6.3 Automated Test Runner
#  Author: James Walsh / Maavsi Dev Team
# ==========================================================

REPORTS_DIR="./reports"
REPORT_FILE="${REPORTS_DIR}/phase_3.6.3_summary.txt"
DATE_NOW=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure Playwright is installed
if ! npx playwright --version &>/dev/null; then
  echo "[ERROR] Playwright not found. Please run: npx playwright install"
  exit 1
fi

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Header
echo "==========================================================" > "$REPORT_FILE"
echo " PHASE 3.6.3 — Automated Calendar Validation Report" >> "$REPORT_FILE"
echo " Generated: $DATE_NOW" >> "$REPORT_FILE"
echo "==========================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Run tests sequentially
echo "[1/4] Running calendar_scroll.spec.js..."
npx playwright test tests/calendar_scroll.spec.js --reporter=list >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

echo "[2/4] Running calendar_interaction.spec.js..."
npx playwright test tests/calendar_interaction.spec.js --reporter=list >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

echo "[3/4] Running calendar_drag.spec.js..."
npx playwright test tests/calendar_drag.spec.js --reporter=list >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

echo "[4/4] Running calendar_color.spec.js..."
npx playwright test tests/calendar_color.spec.js --reporter=list >> "$REPORT_FILE" 2>&1

# Summarize results
echo "" >> "$REPORT_FILE"
echo "==========================================================" >> "$REPORT_FILE"
echo " Test Summary (Pass/Fail):" >> "$REPORT_FILE"
npx playwright show-report >> "$REPORT_FILE" 2>&1
echo "==========================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "All results logged to: $REPORT_FILE"
echo "Open with: open $REPORT_FILE"
echo ""

# Optional: open Playwright HTML report in browser
if [ "$1" == "--view" ]; then
  npx playwright show-report
fi
