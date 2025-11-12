# Phase 3.10: Elite QA Endurance & Stress Testing

## Overview

Phase 3.10 is a comprehensive 180-minute (3-hour) continuous stress test designed to prove ComplyEur's Excel-based 90/180-day calculation logic remains **mathematically flawless and stable** under extended operational stress.

## Mission

The Elite QA Task Force (Phase 3.10) verifies:

- ✅ **Mathematical precision** remains constant through every iteration
- ✅ **No drift, corruption, or memory leaks** after thousands of calculations
- ✅ **Frontend and backend remain fully synchronized** even under rapid, repeated updates
- ✅ **Exports remain byte-for-byte accurate** with backend data throughout
- ✅ **Excel imports** (100–500 employees) maintain 100% computational parity

## Test Modules

### 1️⃣ Excel Import Load Testing

- Generates Excel datasets for 100, 250, and 500 employees with randomized travel data
- Verifies imported record counts, processing times, and CPU usage
- Confirms imported totals match verified Excel formulas
- Detects any rounding or conversion inconsistencies
- Introduces malformed or duplicate data to validate resilience

### 2️⃣ Backend Stability & Memory Integrity

- Runs continuous recalculations for each dataset for the full 180-minute cycle
- Measures floating-point drift (tolerance ≤ 0.0000001)
- Logs memory and CPU performance every 60 seconds
- Detects deadlocks, lag spikes, or concurrency issues
- Confirms SQLite write operations remain stable across duration

### 3️⃣ Frontend Synchronization Stress

- Uses Playwright to simulate 10,000+ UI interactions over the test duration
- Continuously cross-checks backend vs. displayed totals and compliance indicators
- Monitors for any lag >50ms or state desynchronization
- Validates live color-coded risk bars remain accurate after each recalculation

### 4️⃣ Export & Reporting Validation

- Automatically exports CSV and PDF every 5 minutes during the test
- Performs byte-level diff against backend state
- Confirms file integrity, totals, and timestamps
- Tracks export time and size drift to detect I/O slowdowns

## Running the Test

### Quick Start

```bash
# Run with default 180-minute duration
bash scripts/run_phase_3_10_endurance.sh
```

### Custom Duration

```bash
# Set duration in minutes (e.g., 60 minutes for quick test)
export TEST_DURATION_MINUTES=60
bash scripts/run_phase_3_10_endurance.sh
```

### Direct Python Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run with custom parameters
python tests/qa_elite/phase_3_10_endurance_stress.py \
    --db-path data/eu_tracker.db \
    --app-url http://127.0.0.1:5001 \
    --admin-password admin123 \
    --duration 180
```

### Environment Variables

- `TEST_DURATION_MINUTES` - Test duration in minutes (default: 180)
- `APP_URL` - Flask application URL (default: http://127.0.0.1:5001)
- `DATABASE_PATH` - Path to SQLite database (default: data/eu_tracker.db)
- `ADMIN_PASSWORD` - Admin password for login (default: admin123)

## Prerequisites

### Required Dependencies

- Python 3.8+
- Flask application running (or script will start it automatically)
- SQLite database initialized
- Required Python packages (install via `pip install -r requirements.txt`):
  - `psutil` - System monitoring
  - `pandas` - Data analysis
  - `matplotlib` - Memory graph generation
  - `openpyxl` - Excel file generation
  - `playwright` - Frontend automation (optional but recommended)
  - `diff-match-patch` - Export diff comparison (optional)

### Optional Dependencies

- `playwright` - Required for frontend synchronization tests
- `diff-match-patch` - Enhanced CSV diff reporting
- `matplotlib` - Memory graph visualization

The test will gracefully skip modules if optional dependencies are missing.

## Output Reports

After completion, the test generates comprehensive reports in `reports/qa_elite/endurance/`:

### 1. HTML Report (`qa_endurance_report_TIMESTAMP.html`)
- Full summary dashboard with all test results
- System metrics and performance data
- Error logs and drift detections
- Visual status indicators (success/warning/error)

### 2. JSON Metrics (`qa_endurance_metrics_TIMESTAMP.json`)
- Complete test results in machine-readable format
- System performance metrics
- Detailed error logs
- Drift detection records

### 3. Memory Graph (`qa_memory_graph_TIMESTAMP.png`)
- Memory usage over time visualization
- Detects memory leaks and growth patterns
- Falls back to text format if matplotlib unavailable

### 4. Drift Summary (`qa_drift_summary_TIMESTAMP.txt`)
- Floating-point drift log (if any detected)
- Baseline vs. current value comparisons
- Tolerance thresholds and violation details

### 5. Export Diff Log (`qa_export_diff_TIMESTAMP.log`)
- Export verification results
- CSV and PDF consistency checks
- Byte-level diff analysis

## Success Criteria

The test is considered successful if:

- ✅ **Zero numeric drift** - All calculations remain stable
- ✅ **Zero UI desync** - Frontend and backend stay synchronized
- ✅ **Zero export discrepancy** - All exports match backend state
- ✅ **Full system uptime** - No crashes or unhandled exceptions during entire duration

## Troubleshooting

### Flask App Not Running

The script will attempt to start the Flask server automatically. If it fails:

```bash
# Start Flask manually
python run_local.py
```

### Playwright Not Available

Frontend synchronization tests will be skipped. To enable:

```bash
# Install Playwright
pip install playwright
playwright install chromium
```

### Memory Issues

If memory usage grows excessively:

1. Check for memory leaks in calculation logic
2. Review system metrics in JSON report
3. Consider reducing test duration for initial runs

### Database Lock Errors

If SQLite lock errors occur:

1. Ensure no other processes are accessing the database
2. Check for long-running transactions
3. Review deadlock counts in backend stability metrics

## Test Philosophy

- **"Failure is a signal, not an endpoint."** - Every discrepancy must be traced to root cause
- **"Repeat until perfect."** - Iterate until all issues are resolved
- **"All output must withstand EU-level audit scrutiny."** - Reports must be comprehensive and auditable

## Integration with CI/CD

For continuous integration, run shorter duration tests:

```bash
# 10-minute smoke test
export TEST_DURATION_MINUTES=10
bash scripts/run_phase_3_10_endurance.sh
```

## Support

For issues or questions about Phase 3.10 testing:

1. Review the HTML report for detailed error information
2. Check the JSON metrics file for machine-readable data
3. Examine drift summary and export diff logs for specific issues
4. Review test logs in console output

## Related Documentation

- [Excel Import System README](../../../docs/IMPORT_SYSTEM_README.md)
- [Backend Calculation Integrity](../qa_elite/backend_calculation_integrity.py)
- [Export Validation](../qa_elite/export_validation.py)

---

**Phase 3.10 Status:** ✅ Complete and Ready for Execution

**Last Updated:** 2024

