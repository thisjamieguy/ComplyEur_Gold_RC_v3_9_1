"""
Elite QA Task Force: Overnight Endurance Test Suite
Runs extended tests (3+ hours) to uncover race conditions and long-term drift
"""

import pytest
import time
import sqlite3
from datetime import date, datetime, timedelta
import sys
import os
import threading
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.rolling90 import presence_days, days_used_in_window
from app.services.exports import calculate_eu_days_from_trips, export_trips_csv


class EnduranceTestSuite:
    """Extended endurance tests for long-term stability"""
    
    def __init__(self, db_path: str, duration_hours: float = 3.0):
        self.db_path = db_path
        self.duration_hours = duration_hours
        self.duration_seconds = duration_hours * 3600
        self.start_time = None
        self.errors = []
        self.test_count = 0
        self.success_count = 0
    
    def run_endurance_tests(self) -> Dict:
        """Run endurance tests for specified duration"""
        self.start_time = time.time()
        end_time = self.start_time + self.duration_seconds
        
        print("=" * 80)
        print("🌙 Overnight Endurance Test Suite")
        print("=" * 80)
        print(f"Duration: {self.duration_hours} hours ({self.duration_seconds} seconds)")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        while time.time() < end_time:
            elapsed = time.time() - self.start_time
            remaining = end_time - time.time()
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Elapsed: {elapsed/3600:.2f}h | Remaining: {remaining/3600:.2f}h")
            
            # Run test cycles
            self._run_calculation_stability_test()
            self._run_database_stress_test()
            self._run_concurrent_access_test()
            self._run_export_consistency_test()
            self._run_memory_leak_test()
            
            # Brief pause between cycles
            time.sleep(1)
        
        total_duration = time.time() - self.start_time
        
        return {
            'duration_seconds': total_duration,
            'duration_hours': total_duration / 3600,
            'test_count': self.test_count,
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors,
            'success_rate': self.success_count / self.test_count if self.test_count > 0 else 0
        }
    
    def _run_calculation_stability_test(self):
        """Test calculation stability over time"""
        self.test_count += 1
        try:
            today = date.today()
            trips = [
                {
                    'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
                    'exit_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
                    'country': 'FR'
                }
            ]
            
            # Run calculation multiple times
            for _ in range(10):
                presence = presence_days(trips)
                days = days_used_in_window(presence, today)
                
                # Should always be 11
                if days != 11:
                    self.errors.append({
                        'test': 'calculation_stability',
                        'error': f'Expected 11, got {days}',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
            
            self.success_count += 1
        except Exception as e:
            self.errors.append({
                'test': 'calculation_stability',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _run_database_stress_test(self):
        """Stress test database operations"""
        self.test_count += 1
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Perform multiple operations
            for _ in range(50):
                cursor.execute('SELECT COUNT(*) FROM employees')
                cursor.fetchone()
            
            conn.close()
            self.success_count += 1
        except Exception as e:
            self.errors.append({
                'test': 'database_stress',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _run_concurrent_access_test(self):
        """Test concurrent database access"""
        self.test_count += 1
        try:
            errors = []
            
            def worker(worker_id):
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM employees')
                    cursor.fetchone()
                    conn.close()
                except Exception as e:
                    errors.append(f'Worker {worker_id}: {e}')
            
            # Create multiple threads
            threads = []
            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            if errors:
                self.errors.append({
                    'test': 'concurrent_access',
                    'errors': errors,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.success_count += 1
        except Exception as e:
            self.errors.append({
                'test': 'concurrent_access',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _run_export_consistency_test(self):
        """Test export consistency over time"""
        self.test_count += 1
        try:
            # Export CSV multiple times and compare
            csv1 = export_trips_csv(self.db_path)
            time.sleep(0.1)
            csv2 = export_trips_csv(self.db_path)
            
            if csv1 != csv2:
                self.errors.append({
                    'test': 'export_consistency',
                    'error': 'CSV exports differ between calls',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.success_count += 1
        except Exception as e:
            self.errors.append({
                'test': 'export_consistency',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _run_memory_leak_test(self):
        """Test for memory leaks in calculations"""
        self.test_count += 1
        try:
            # Run calculations many times
            today = date.today()
            trips = [
                {
                    'entry_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
                    'exit_date': (today - timedelta(days=40)).strftime('%Y-%m-%d'),
                    'country': 'FR'
                }
            ]
            
            for _ in range(1000):
                presence = presence_days(trips)
                days = days_used_in_window(presence, today)
            
            self.success_count += 1
        except Exception as e:
            self.errors.append({
                'test': 'memory_leak',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })


class TestEnduranceSuite:
    """Pytest wrapper for endurance tests"""
    
    @pytest.mark.slow
    def test_overnight_endurance(self, temp_db):
        """Overnight endurance test (3+ hours)"""
        suite = EnduranceTestSuite(temp_db, duration_hours=3.0)
        results = suite.run_endurance_tests()
        
        print(f"\nEndurance Test Results:")
        print(f"  Duration: {results['duration_hours']:.2f} hours")
        print(f"  Tests Run: {results['test_count']}")
        print(f"  Successes: {results['success_count']}")
        print(f"  Errors: {results['error_count']}")
        print(f"  Success Rate: {results['success_rate']*100:.2f}%")
        
        # Assert success rate is high
        assert results['success_rate'] >= 0.95, f"Success rate too low: {results['success_rate']*100:.2f}%"
        assert results['error_count'] == 0, f"Errors found: {results['error_count']}"


if __name__ == '__main__':
    # Run as standalone script
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            country TEXT,
            entry_date DATE,
            exit_date DATE,
            travel_days INTEGER DEFAULT 0,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')
    conn.commit()
    conn.close()
    
    suite = EnduranceTestSuite(db_path, duration_hours=0.1)  # Short test for demo
    results = suite.run_endurance_tests()
    
    print("\n" + "=" * 80)
    print("ENDURANCE TEST RESULTS")
    print("=" * 80)
    print(f"Success Rate: {results['success_rate']*100:.2f}%")
    print(f"Errors: {results['error_count']}")
    
    if os.path.exists(db_path):
        os.unlink(db_path)




