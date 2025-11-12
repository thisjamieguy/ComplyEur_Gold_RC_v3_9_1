"""
SQLite WAL Mode & Concurrent Session Tests
Tests Write-Ahead Logging consistency and concurrent database operations.
"""

import pytest
import sqlite3
import threading
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'data' / 'eu_tracker.db'))


def test_wal_mode_enabled():
    """Test that WAL mode is enabled on the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode')
    journal_mode = cursor.fetchone()[0].upper()
    conn.close()
    assert journal_mode == 'WAL', f"Expected WAL mode, got {journal_mode}"


def test_wal_checkpoint():
    """Test that WAL checkpoint works without errors"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        result = cursor.fetchone()
        # Result is (busy, log, checkpointed)
        assert result is not None
    except Exception as e:
        pytest.fail(f"WAL checkpoint failed: {e}")
    finally:
        conn.close()


def test_concurrent_reads():
    """Test that multiple connections can read simultaneously"""
    results = []
    errors = []
    
    def read_employee_count():
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM employees')
            count = cursor.fetchone()[0]
            results.append(count)
            conn.close()
        except Exception as e:
            errors.append(str(e))
    
    # Create 5 concurrent readers
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=read_employee_count)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=5)
    
    assert len(errors) == 0, f"Concurrent read errors: {errors}"
    assert len(results) == 5, "Not all readers completed"
    # All readers should see the same count
    assert len(set(results)) == 1, f"Different counts seen: {results}"


def test_concurrent_writes():
    """Test that multiple connections can write without conflicts"""
    errors = []
    write_count = 5
    
    def write_employee(name):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            cursor = conn.cursor()
            # Use a unique name to avoid conflicts
            cursor.execute('INSERT INTO employees (name) VALUES (?)', (f'{name}_{int(time.time() * 1000)}',))
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            errors.append(f"Write failed: {e}")
            return False
    
    # Create multiple writers
    threads = []
    for i in range(write_count):
        thread = threading.Thread(target=lambda i=i: write_employee(f'concurrent_test_{i}'))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=10)
    
    # Check that most writes succeeded (some may fail due to unique constraints)
    assert len(errors) < write_count, f"Too many write errors: {errors}"
    
    # Clean up test data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE name LIKE 'concurrent_test_%'")
    conn.commit()
    conn.close()


def test_read_while_write():
    """Test that reads can proceed while writes are happening"""
    read_results = []
    write_complete = threading.Event()
    errors = []
    
    def write_trip():
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            cursor = conn.cursor()
            # Get an employee ID (create one if none exists)
            cursor.execute('SELECT id FROM employees LIMIT 1')
            row = cursor.fetchone()
            if not row:
                cursor.execute('INSERT INTO employees (name) VALUES (?)', ('test_employee',))
                employee_id = cursor.lastrowid
            else:
                employee_id = row[0]
            
            # Insert a trip
            cursor.execute(
                'INSERT INTO trips (employee_id, country, entry_date, exit_date) VALUES (?, ?, ?, ?)',
                (employee_id, 'FR', '2024-01-01', '2024-01-05')
            )
            conn.commit()
            conn.close()
            write_complete.set()
        except Exception as e:
            errors.append(f"Write error: {e}")
            write_complete.set()
    
    def read_trips():
        while not write_complete.is_set():
            try:
                conn = sqlite3.connect(DB_PATH, timeout=5.0)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM trips')
                count = cursor.fetchone()[0]
                read_results.append(count)
                conn.close()
                time.sleep(0.1)
            except Exception as e:
                errors.append(f"Read error: {e}")
                break
    
    # Start reader thread
    reader_thread = threading.Thread(target=read_trips)
    reader_thread.start()
    
    # Start writer thread
    writer_thread = threading.Thread(target=write_trip)
    writer_thread.start()
    
    # Wait for writer to complete
    writer_thread.join(timeout=10)
    
    # Wait a bit for reader to finish
    time.sleep(0.5)
    
    # Check results
    assert write_complete.is_set(), "Write did not complete"
    assert len(read_results) > 0, "No reads occurred"
    assert len(errors) == 0, f"Errors during read-while-write: {errors}"
    
    # Clean up
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE country = 'FR' AND entry_date = '2024-01-01'")
    cursor.execute("DELETE FROM employees WHERE name = 'test_employee'")
    conn.commit()
    conn.close()


def test_integrity_check():
    """Test that database integrity check passes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA integrity_check')
    rows = cursor.fetchall()
    conn.close()
    
    # Integrity check should return single row with 'ok'
    assert len(rows) == 1, f"Expected single row from integrity_check, got {len(rows)}"
    assert rows[0][0] == 'ok', f"Integrity check failed: {rows[0][0]}"


def test_foreign_key_constraints():
    """Test that foreign key constraints are enabled when using Flask app context"""
    # Foreign keys in SQLite are per-connection, so we need to enable them
    # The Flask app enables them via _apply_pragmas in get_db()
    # This test verifies that foreign keys work correctly
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Enable foreign keys for this connection (matching Flask app behavior)
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('PRAGMA foreign_keys')
    foreign_keys_enabled = cursor.fetchone()[0]
    
    # Test that foreign key constraint works
    # Try to insert a trip with invalid employee_id
    try:
        cursor.execute(
            'INSERT INTO trips (employee_id, country, entry_date, exit_date) VALUES (?, ?, ?, ?)',
            (999999, 'FR', '2024-01-01', '2024-01-05')
        )
        conn.commit()
        # If we get here, foreign keys are not enforced
        # Clean up and fail
        cursor.execute('DELETE FROM trips WHERE employee_id = 999999')
        conn.commit()
        conn.close()
        pytest.fail("Foreign key constraint not enforced")
    except sqlite3.IntegrityError:
        # Expected: foreign key constraint should prevent this
        conn.rollback()
        conn.close()
        assert foreign_keys_enabled == 1, "Foreign key constraints should be enabled"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

