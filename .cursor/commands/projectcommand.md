# projectcommand

Write your command content here.

This command will be available in chat with /projectcommand

commands:
  - name: 🧪 Run All Tests
    description: Run full Playwright + Bash test suite and generate summary report
    run: bash scripts/run_phase_tests.sh

  - name: 🚀 Start Flask Server
    description: Launch local Flask app at port 5001
    run: flask run --port=5001

  - name: 💾 Backup Database
    description: Create timestamped backup of the SQLite database
    run: python scripts/backup_db.py

  - name: 📊 Generate Compliance Report
    description: Export summary of employee travel days and 90/180 status
    run: python backend/export_report.py

  - name: 🧹 Clean Old Builds
    description: Move outdated versions into /archive and clear caches
    run: bash scripts/cleanup_old_versions.sh