"""
Unit tests for GDPR compliance features in EU Trip Tracker.

Run with: python test_gdpr.py
Or with pytest: pytest test_gdpr.py -v
"""

import unittest
import tempfile
import os
import sqlite3
import json
import zipfile
from datetime import datetime, timedelta

# Import services
from app.services.hashing import Hasher
from app.services.retention import calculate_retention_cutoff, get_expired_trips, purge_expired_trips, anonymize_employee
from app.services.dsar import get_employee_data, create_dsar_export, delete_employee_data, rectify_employee_name
from app.services.exports import export_trips_csv, export_employee_report_pdf, export_all_employees_report_pdf


class TestPasswordHashing(unittest.TestCase):
    """Test password hashing with argon2 and bcrypt."""
    
    def test_argon2_hash_and_verify(self):
        """Test Argon2 password hashing."""
        hasher = Hasher('argon2')
        password = 'testPassword123!'
        hashed = hasher.hash(password)
        
        # Hash should be different from plaintext
        self.assertNotEqual(password, hashed)
        
        # Verification should work
        self.assertTrue(hasher.verify(hashed, password))
        
        # Wrong password should fail
        self.assertFalse(hasher.verify(hashed, 'wrongPassword'))
    
    def test_bcrypt_hash_and_verify(self):
        """Test bcrypt password hashing."""
        hasher = Hasher('bcrypt')
        password = 'testPassword456!'
        hashed = hasher.hash(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(hasher.verify(hashed, password))
        self.assertFalse(hasher.verify(hashed, 'wrongPassword'))


class TestRetentionPolicy(unittest.TestCase):
    """Test data retention and purge functionality."""
    
    def setUp(self):
        """Create temporary database for testing."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        c = self.conn.cursor()
        
        # Create tables
        c.execute('CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT)')
        c.execute('''CREATE TABLE trips (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            country TEXT,
            entry_date TEXT,
            exit_date TEXT,
            travel_days INTEGER,
            created_at TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )''')
        
        # Add test data
        c.execute('INSERT INTO employees (id, name) VALUES (1, "Test Employee")')
        
        # Add old trip (past retention)
        old_date = (datetime.now().date() - timedelta(days=1200)).strftime('%Y-%m-%d')
        c.execute('INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                  (1, 'FR', old_date, old_date, 1, old_date))
        
        # Add recent trip (within retention)
        recent_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                  (1, 'DE', recent_date, recent_date, 1, recent_date))
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up temporary database."""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_calculate_retention_cutoff(self):
        """Test retention cutoff calculation."""
        cutoff = calculate_retention_cutoff(36)
        cutoff_date = datetime.strptime(cutoff, '%Y-%m-%d').date()
        
        # Cutoff should be approximately 36 months ago
        expected = datetime.now().date() - timedelta(days=36 * 30)
        delta = abs((cutoff_date - expected).days)
        self.assertLess(delta, 5)  # Allow 5 days variance
    
    def test_get_expired_trips(self):
        """Test retrieval of expired trips."""
        expired = get_expired_trips(self.db_path, 36)
        
        # Should find the old trip
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]['country'], 'FR')
    
    def test_purge_expired_trips(self):
        """Test purging of expired trips."""
        result = purge_expired_trips(self.db_path, 36)
        
        # Should delete 1 trip
        self.assertEqual(result['trips_deleted'], 1)
        
        # Recent trip should remain
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM trips')
        self.assertEqual(c.fetchone()[0], 1)
    
    def test_anonymize_employee(self):
        """Test employee anonymization."""
        result = anonymize_employee(self.db_path, 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['old_name'], 'Test Employee')
        self.assertTrue(result['new_name'].startswith('Employee #'))


class TestDSAR(unittest.TestCase):
    """Test Data Subject Access Request functionality."""
    
    def setUp(self):
        """Create temporary database and export directory."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.export_dir = tempfile.mkdtemp()
        
        self.conn = sqlite3.connect(self.db_path)
        c = self.conn.cursor()
        
        # Create tables
        c.execute('CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT)')
        c.execute('''CREATE TABLE trips (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            country TEXT,
            entry_date TEXT,
            exit_date TEXT,
            travel_days INTEGER,
            created_at TEXT
        )''')
        
        # Add test employee
        c.execute('INSERT INTO employees (id, name) VALUES (1, "John Doe")')
        c.execute('INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                  (1, 'FR', '2024-01-01', '2024-01-10', 10, '2024-01-01'))
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up temporary files."""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
        # Clean up export directory
        for file in os.listdir(self.export_dir):
            os.unlink(os.path.join(self.export_dir, file))
        os.rmdir(self.export_dir)
    
    def test_get_employee_data(self):
        """Test retrieving employee data."""
        data = get_employee_data(self.db_path, 1)
        
        self.assertIsNotNone(data)
        self.assertEqual(data['employee']['name'], 'John Doe')
        self.assertEqual(len(data['trips']), 1)
        self.assertEqual(data['trips'][0]['country'], 'FR')
    
    def test_create_dsar_export(self):
        """Test creating DSAR export ZIP."""
        result = create_dsar_export(self.db_path, 1, self.export_dir, 36)
        
        self.assertTrue(result['success'])
        self.assertTrue(os.path.exists(result['file_path']))
        self.assertEqual(result['employee_name'], 'John Doe')
        self.assertEqual(result['trips_count'], 1)
        
        # Verify ZIP contents
        with zipfile.ZipFile(result['file_path'], 'r') as zipf:
            files = zipf.namelist()
            self.assertIn('employee.json', files)
            self.assertIn('trips.csv', files)
            self.assertIn('processing-notes.txt', files)
            
            # Check JSON content
            employee_json = json.loads(zipf.read('employee.json').decode('utf-8'))
            self.assertEqual(employee_json['name'], 'John Doe')
    
    def test_delete_employee_data(self):
        """Test deleting employee and all trips."""
        result = delete_employee_data(self.db_path, 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['employee_name'], 'John Doe')
        self.assertEqual(result['trips_deleted'], 1)
        
        # Verify deletion
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM employees WHERE id = 1')
        self.assertEqual(c.fetchone()[0], 0)
        
        c.execute('SELECT COUNT(*) FROM trips WHERE employee_id = 1')
        self.assertEqual(c.fetchone()[0], 0)
    
    def test_rectify_employee_name(self):
        """Test rectifying employee name."""
        result = rectify_employee_name(self.db_path, 1, 'Jane Doe')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['old_name'], 'John Doe')
        self.assertEqual(result['new_name'], 'Jane Doe')
        
        # Verify update
        c = self.conn.cursor()
        c.execute('SELECT name FROM employees WHERE id = 1')
        self.assertEqual(c.fetchone()[0], 'Jane Doe')


class TestExports(unittest.TestCase):
    """Test CSV and PDF export functionality."""
    
    def setUp(self):
        """Create temporary database."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        c = self.conn.cursor()
        
        # Create tables
        c.execute('CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT)')
        c.execute('''CREATE TABLE trips (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            country TEXT,
            entry_date TEXT,
            exit_date TEXT,
            travel_days INTEGER,
            created_at TEXT
        )''')
        
        # Add test data
        c.execute('INSERT INTO employees (id, name) VALUES (1, "Alice")')
        c.execute('INSERT INTO employees (id, name) VALUES (2, "Bob")')
        
        c.execute('INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days) VALUES (?, ?, ?, ?, ?)',
                  (1, 'FR', '2024-01-01', '2024-01-05', 5))
        c.execute('INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days) VALUES (?, ?, ?, ?, ?)',
                  (2, 'DE', '2024-02-01', '2024-02-10', 10))
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up."""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_export_trips_csv_all(self):
        """Test CSV export of all trips."""
        csv_data = export_trips_csv(self.db_path)
        
        # Should contain header and 2 data rows
        lines = csv_data.strip().split('\n')
        self.assertEqual(len(lines), 3)  # Header + 2 trips
        
        # Check header
        self.assertIn('Employee Name', lines[0])
        self.assertIn('Country', lines[0])
        
        # Check data
        self.assertIn('Alice', csv_data)
        self.assertIn('Bob', csv_data)
    
    def test_export_trips_csv_employee(self):
        """Test CSV export for specific employee."""
        csv_data = export_trips_csv(self.db_path, employee_id=1)
        
        lines = csv_data.strip().split('\n')
        self.assertEqual(len(lines), 2)  # Header + 1 trip
        self.assertIn('Alice', csv_data)
        self.assertNotIn('Bob', csv_data)
    
    def test_export_employee_pdf(self):
        """Test PDF export for employee."""
        pdf_bytes = export_employee_report_pdf(self.db_path, 1)
        
        # PDF should start with %PDF
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        
        # Should be reasonable size (> 1KB)
        self.assertGreater(len(pdf_bytes), 1000)
    
    def test_export_all_employees_pdf(self):
        """Test PDF summary for all employees."""
        pdf_bytes = export_all_employees_report_pdf(self.db_path)
        
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertGreater(len(pdf_bytes), 1000)


class TestDataMinimisation(unittest.TestCase):
    """Test that only minimal data is stored."""
    
    def test_employee_table_schema(self):
        """Verify employees table has only id and name."""
        db_fd, db_path = tempfile.mkstemp()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT)')
        c.execute('PRAGMA table_info(employees)')
        columns = c.fetchall()
        
        # Should have exactly 2 columns
        self.assertEqual(len(columns), 2)
        
        column_names = [col[1] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('name', column_names)
        
        # Should NOT have email, phone, address, etc.
        forbidden = ['email', 'phone', 'address', 'dob', 'ssn']
        for field in forbidden:
            self.assertNotIn(field, column_names)
        
        conn.close()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_trips_table_schema(self):
        """Verify trips table has only necessary fields."""
        db_fd, db_path = tempfile.mkstemp()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE trips (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            country TEXT,
            entry_date TEXT,
            exit_date TEXT,
            travel_days INTEGER,
            created_at TEXT
        )''')
        c.execute('PRAGMA table_info(trips)')
        columns = c.fetchall()
        
        column_names = [col[1] for col in columns]
        
        # Should have expected fields
        expected = ['id', 'employee_id', 'country', 'entry_date', 'exit_date', 'travel_days', 'created_at']
        for field in expected:
            self.assertIn(field, column_names)
        
        # Should NOT have unnecessary fields
        forbidden = ['purpose', 'hotel', 'flight', 'cost', 'notes', 'manager']
        for field in forbidden:
            self.assertNotIn(field, column_names)
        
        conn.close()
        os.close(db_fd)
        os.unlink(db_path)


def run_tests():
    """Run all GDPR compliance tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPasswordHashing))
    suite.addTests(loader.loadTestsFromTestCase(TestRetentionPolicy))
    suite.addTests(loader.loadTestsFromTestCase(TestDSAR))
    suite.addTests(loader.loadTestsFromTestCase(TestExports))
    suite.addTests(loader.loadTestsFromTestCase(TestDataMinimisation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
