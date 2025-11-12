#!/usr/bin/env bash
set -euo pipefail
echo "Running lint + unit + diff + e2e + perf..."
ruff check .
pytest -q --maxfail=1 --disable-warnings --tb=short --html=tests/reports/pytest_report.html --self-contained-html
npx playwright test --config=playwright.config.ts --reporter=html
echo "✅ All tests complete"
