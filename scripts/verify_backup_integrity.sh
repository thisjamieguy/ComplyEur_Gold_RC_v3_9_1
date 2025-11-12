#!/bin/bash
# Verify Encrypted Backup Integrity
# Phase 2: Data Protection & Encryption

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKUP_DIR="${BACKUP_DIR:-./data/backups}"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    # Find most recent encrypted backup
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.db.encrypted 2>/dev/null | head -1)
    
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "${RED}Error: No encrypted backups found in $BACKUP_DIR${NC}"
        echo "Usage: $0 [backup_file.encrypted]"
        exit 1
    fi
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Verifying encrypted backup: $BACKUP_FILE${NC}"
echo ""

# Check file exists and is readable
if [ ! -r "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ Backup file is not readable${NC}"
    exit 1
fi

# Check file size
FILE_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
if [ "$FILE_SIZE" -lt 100 ]; then
    echo -e "${RED}✗ Backup file is too small (may be corrupted)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ File exists and has valid size: ${FILE_SIZE} bytes${NC}"

# Verify using Python script
python3 << EOF
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backup_encrypted import verify_backup_integrity

result = verify_backup_integrity("$BACKUP_FILE")

if result.get('success') and result.get('valid'):
    print(f"\n${GREEN}✓ Backup integrity verified${NC}")
    print(f"  - Tables found: {result.get('tables_found', 0)}")
    print(f"  - Backup size: {result.get('backup_size_bytes', 0)} bytes")
    sys.exit(0)
else:
    print(f"\n${RED}✗ Backup verification failed${NC}")
    print(f"  Error: {result.get('error', 'Unknown error')}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ All checks passed${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Verification failed${NC}"
    exit 1
fi

