#!/bin/bash
# Daily Log Integrity Check
# Phase 5: Compliance & Monitoring
# Runs SHA-256 integrity check on all audit logs

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="${LOG_DIR:-logs}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${YELLOW}🔒 Daily Log Integrity Check${NC}"
echo "=================================="
echo "Timestamp: $TIMESTAMP"
echo "Log Directory: $LOG_DIR"
echo ""

# Run Python integrity checker
python3 << EOF
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.services.logging.integrity_checker import get_integrity_checker

log_dir = os.getenv('LOG_DIR', 'logs')
checker = get_integrity_checker(log_dir)

print("Running daily integrity check...")
summary = checker.daily_integrity_check()

print(f"\n✅ Integrity Check Complete")
print(f"Date: {summary['date']}")
print(f"Total Files: {summary['total_files']}")
print(f"Valid Files: {summary['valid_files']}")
print(f"Invalid Files: {summary['invalid_files']}")

if summary['invalid_files'] > 0:
    print(f"\n⚠️  WARNING: {summary['invalid_files']} file(s) failed integrity check!")
    for log_file, result in summary['checks'].items():
        if result.get('status') != 'valid' and result.get('status') != 'new':
            print(f"  - {log_file}: {result.get('status')}")
            if 'warning' in result:
                print(f"    {result['warning']}")
    sys.exit(1)
else:
    print("\n✅ All log files passed integrity check")
    sys.exit(0)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ Daily integrity check passed${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Integrity check failed - investigate immediately!${NC}"
    exit 1
fi

