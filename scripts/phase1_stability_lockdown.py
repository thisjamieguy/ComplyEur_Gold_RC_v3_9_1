#!/usr/bin/env python3
"""
Phase 1 Stability Lockdown Script
Executes comprehensive stability checks for ComplyEur v3.9.1
"""

import os
import sys
import sqlite3
import subprocess
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'data' / 'eu_tracker.db'))
AUTH_DB_PATH = os.getenv('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
if not AUTH_DB_PATH:
    AUTH_DB_PATH = str(PROJECT_ROOT / 'data' / 'auth.db')

REPORTS_DIR = PROJECT_ROOT / 'docs' / 'testing' / 'phase1_final'
SCREENSHOTS_DIR = PROJECT_ROOT / 'docs' / 'testing' / 'screenshots' / 'phase1_manual'

def ensure_dirs():
    """Ensure report directories exist"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def check_wal_mode(db_path: str) -> dict:
    """Check if WAL mode is enabled"""
    result = {'enabled': False, 'journal_mode': 'unknown', 'error': None}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode')
        result['journal_mode'] = cursor.fetchone()[0].upper()
        result['enabled'] = result['journal_mode'] == 'WAL'
        conn.close()
    except Exception as e:
        result['error'] = str(e)
    return result

def run_integrity_check(db_path: str) -> dict:
    """Run PRAGMA integrity_check"""
    result = {'ok': False, 'errors': [], 'message': ''}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA integrity_check')
        rows = cursor.fetchall()
        if len(rows) == 1 and rows[0][0] == 'ok':
            result['ok'] = True
            result['message'] = 'ok'
        else:
            result['errors'] = [row[0] for row in rows]
            result['message'] = '\n'.join([row[0] for row in rows])
        conn.close()
    except Exception as e:
        result['error'] = str(e)
        result['message'] = f'Error running integrity check: {e}'
    return result

def get_schema_info(db_path: str) -> dict:
    """Get detailed schema information"""
    schema = {'tables': [], 'error': None}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get table info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            for col in cursor.fetchall():
                columns.append({
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': bool(col[3]),
                    'default_value': col[4],
                    'pk': bool(col[5])
                })
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = [row[1] for row in cursor.fetchall()]
            
            schema['tables'].append({
                'name': table,
                'columns': columns,
                'indexes': indexes
            })
        
        conn.close()
    except Exception as e:
        schema['error'] = str(e)
    return schema

def checkpoint_and_vacuum(db_path: str) -> dict:
    """Force checkpoint and vacuum"""
    result = {'checkpoint': False, 'vacuum': False, 'error': None}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Checkpoint
        try:
            cursor.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            result['checkpoint'] = True
        except Exception as e:
            result['checkpoint_error'] = str(e)
        
        # Get DB size before vacuum
        size_before = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        # Vacuum
        try:
            cursor.execute('VACUUM')
            conn.commit()
            result['vacuum'] = True
        except Exception as e:
            result['vacuum_error'] = str(e)
        
        # Get DB size after vacuum
        size_after = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        result['size_before'] = size_before
        result['size_after'] = size_after
        result['size_reduction'] = size_before - size_after
        
        conn.close()
    except Exception as e:
        result['error'] = str(e)
    return result

def generate_schema_audit_report(db_path: str, output_path: Path):
    """Generate schema audit report"""
    schema = get_schema_info(db_path)
    wal_info = check_wal_mode(db_path)
    integrity = run_integrity_check(db_path)
    
    report = f"""# Schema Audit Report
Generated: {datetime.now().isoformat()}

## Database Information
- **Path**: {db_path}
- **WAL Mode**: {wal_info['journal_mode']} ({'Enabled' if wal_info['enabled'] else 'Disabled'})
- **Integrity Check**: {'PASS' if integrity['ok'] else 'FAIL'}
- **Integrity Details**: {integrity['message']}

## Tables

"""
    
    for table in schema['tables']:
        report += f"### {table['name']}\n\n"
        report += "#### Columns\n\n"
        report += "| Name | Type | Not Null | Default | Primary Key |\n"
        report += "|------|------|----------|---------|-------------|\n"
        for col in table['columns']:
            report += f"| {col['name']} | {col['type']} | {col['notnull']} | {col['default_value'] or ''} | {col['pk']} |\n"
        report += "\n"
        if table['indexes']:
            report += f"#### Indexes\n\n"
            for idx in table['indexes']:
                report += f"- {idx}\n"
            report += "\n"
        report += "\n"
    
    if schema['error']:
        report += f"\n## Errors\n\n{schema['error']}\n"
    
    output_path.write_text(report)
    print(f"Schema audit report written to {output_path}")

def main():
    """Main execution"""
    ensure_dirs()
    
    print("=" * 80)
    print("Phase 1 Stability Lockdown - Schema & Database Checks")
    print("=" * 80)
    print()
    
    # Check main database
    print(f"Checking main database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return 1
    
    # WAL Mode
    print("\n1. Checking WAL Mode...")
    wal_info = check_wal_mode(DB_PATH)
    print(f"   Journal Mode: {wal_info['journal_mode']}")
    if wal_info['enabled']:
        print("   ✅ WAL mode is enabled")
    else:
        print(f"   ⚠️  WAL mode is not enabled (current: {wal_info['journal_mode']})")
    
    # Integrity Check
    print("\n2. Running Integrity Check...")
    integrity = run_integrity_check(DB_PATH)
    if integrity['ok']:
        print("   ✅ Integrity check passed")
    else:
        print(f"   ❌ Integrity check failed: {integrity['message']}")
        return 1
    
    # Schema Audit
    print("\n3. Generating Schema Audit...")
    schema_report_path = REPORTS_DIR / 'schema_audit_report.md'
    generate_schema_audit_report(DB_PATH, schema_report_path)
    print(f"   ✅ Schema audit report generated: {schema_report_path}")
    
    # Checkpoint and Vacuum
    print("\n4. Running Checkpoint and Vacuum...")
    cv_result = checkpoint_and_vacuum(DB_PATH)
    if cv_result['checkpoint']:
        print("   ✅ Checkpoint completed")
    else:
        print(f"   ⚠️  Checkpoint failed: {cv_result.get('checkpoint_error', 'Unknown error')}")
    if cv_result['vacuum']:
        print("   ✅ Vacuum completed")
        print(f"   Database size: {cv_result['size_before']} -> {cv_result['size_after']} bytes")
        if cv_result['size_reduction'] > 0:
            print(f"   Size reduction: {cv_result['size_reduction']} bytes")
    else:
        print(f"   ⚠️  Vacuum failed: {cv_result.get('vacuum_error', 'Unknown error')}")
    
    # Save integrity check log
    integrity_log_path = REPORTS_DIR / 'integrity_check.log'
    integrity_log_path.write_text(f"Integrity Check Results\n{'=' * 80}\n\n")
    integrity_log_path.write_text(integrity_log_path.read_text() + f"Timestamp: {datetime.now().isoformat()}\n")
    integrity_log_path.write_text(integrity_log_path.read_text() + f"Status: {'PASS' if integrity['ok'] else 'FAIL'}\n")
    integrity_log_path.write_text(integrity_log_path.read_text() + f"Message: {integrity['message']}\n")
    
    print("\n" + "=" * 80)
    print("Schema & Database Checks Complete")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

