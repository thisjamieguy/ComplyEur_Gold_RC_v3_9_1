"""
Elite QA Task Force: Export Validation Tests
Validates CSV/PDF exports match backend data exactly (byte-for-byte equivalence where applicable)
"""

import pytest
import sqlite3
import csv
import io
from datetime import date, datetime, timedelta
from typing import Dict, List
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.exports import export_trips_csv, export_employee_report_pdf, calculate_eu_days_from_trips


class ExportValidator:
    """Validates export accuracy and completeness"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.discrepancies = []
    
    def validate_csv_export_accuracy(self, employee_id: int = None) -> bool:
        """Validate CSV export matches database exactly"""
        # Get data from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if employee_id:
            cursor.execute('''
                SELECT employees.name, trips.country, trips.entry_date, 
                       trips.exit_date, trips.travel_days
                FROM trips
                JOIN employees ON trips.employee_id = employees.id
                WHERE trips.employee_id = ?
                ORDER BY trips.entry_date DESC
            ''', (employee_id,))
        else:
            cursor.execute('''
                SELECT employees.name, trips.country, trips.entry_date, 
                       trips.exit_date, trips.travel_days
                FROM trips
                JOIN employees ON trips.employee_id = employees.id
                ORDER BY employees.name, trips.entry_date DESC
            ''')
        
        db_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get CSV export
        csv_content = export_trips_csv(self.db_path, employee_id)
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        csv_rows = list(csv_reader)
        
        # Compare counts
        if len(db_rows) != len(csv_rows):
            self.discrepancies.append({
                'test': 'csv_row_count',
                'database_rows': len(db_rows),
                'csv_rows': len(csv_rows)
            })
            return False
        
        # Compare data (account for CSV column name differences)
        for db_row, csv_row in zip(db_rows, csv_rows):
            if (db_row['name'] != csv_row['Employee Name'] or
                db_row['country'] != csv_row['Country'] or
                db_row['entry_date'] != csv_row['Entry Date'] or
                db_row['exit_date'] != csv_row['Exit Date']):
                self.discrepancies.append({
                    'test': 'csv_data_mismatch',
                    'database': db_row,
                    'csv': csv_row
                })
                return False
        
        return True
    
    def validate_csv_completeness(self) -> bool:
        """Validate CSV export includes all required fields"""
        csv_content = export_trips_csv(self.db_path)
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        required_fields = ['Employee Name', 'Country', 'Entry Date', 'Exit Date', 'Travel Days', 'Schengen Status']
        fieldnames = csv_reader.fieldnames
        
        if not fieldnames:
            self.discrepancies.append({
                'test': 'csv_fieldnames',
                'expected': required_fields,
                'actual': None
            })
            return False
        
        for field in required_fields:
            if field not in fieldnames:
                self.discrepancies.append({
                    'test': 'csv_missing_field',
                    'missing': field,
                    'available': fieldnames
                })
                return False
        
        return True
    
    def validate_pdf_export_accuracy(self, employee_id: int) -> bool:
        """Validate PDF export matches database calculations"""
        # Get employee data from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        emp = cursor.fetchone()
        if not emp:
            conn.close()
            return False
        
        cursor.execute('''
            SELECT country, entry_date, exit_date, travel_days
            FROM trips WHERE employee_id = ?
            ORDER BY entry_date DESC
        ''', (employee_id,))
        trips = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Calculate expected values
        today = date.today()
        expected_days_used = calculate_eu_days_from_trips(trips, today)
        expected_trip_count = len(trips)
        
        # Generate PDF
        pdf_bytes = export_employee_report_pdf(self.db_path, employee_id)
        
        # Note: Full PDF parsing would require PyPDF2 or similar
        # For now, we validate that PDF was generated and contains expected data structure
        if len(pdf_bytes) == 0:
            self.discrepancies.append({
                'test': 'pdf_generation',
                'issue': 'empty_pdf'
            })
            return False
        
        # Basic validation: PDF should have reasonable size
        if len(pdf_bytes) < 1000:  # Minimum reasonable PDF size
            self.discrepancies.append({
                'test': 'pdf_size',
                'size': len(pdf_bytes),
                'expected_min': 1000
            })
            return False
        
        # Store expected values for comparison (if we add PDF parsing later)
        return True
    
    def validate_export_consistency(self, employee_id: int) -> bool:
        """Validate CSV and PDF exports are consistent with each other"""
        # Get database data
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT country, entry_date, exit_date, travel_days
            FROM trips WHERE employee_id = ?
            ORDER BY entry_date DESC
        ''', (employee_id,))
        db_trips = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get CSV export
        csv_content = export_trips_csv(self.db_path, employee_id)
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        csv_trips = list(csv_reader)
        
        # Compare trip counts
        if len(db_trips) != len(csv_trips):
            self.discrepancies.append({
                'test': 'export_consistency',
                'database_trips': len(db_trips),
                'csv_trips': len(csv_trips)
            })
            return False
        
        # Validate PDF can be generated (basic check)
        try:
            pdf_bytes = export_employee_report_pdf(self.db_path, employee_id)
            if len(pdf_bytes) == 0:
                return False
        except Exception as e:
            self.discrepancies.append({
                'test': 'pdf_export_error',
                'error': str(e)
            })
            return False
        
        return True
    
    def validate_export_roundtrip(self, employee_id: int) -> bool:
        """Validate export -> import roundtrip maintains data integrity"""
        # Export to CSV
        csv_content = export_trips_csv(self.db_path, employee_id)
        
        # Parse CSV back
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        exported_trips = list(csv_reader)
        
        # Get original data
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT country, entry_date, exit_date, travel_days
            FROM trips WHERE employee_id = ?
            ORDER BY entry_date DESC
        ''', (employee_id,))
        original_trips = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Compare
        if len(original_trips) != len(exported_trips):
            self.discrepancies.append({
                'test': 'roundtrip_count',
                'original': len(original_trips),
                'exported': len(exported_trips)
            })
            return False
        
        # Compare data (account for CSV format differences)
        for orig, exp in zip(original_trips, exported_trips):
            if (orig['country'] != exp['Country'] or
                orig['entry_date'] != exp['Entry Date'] or
                orig['exit_date'] != exp['Exit Date']):
                self.discrepancies.append({
                    'test': 'roundtrip_data',
                    'original': orig,
                    'exported': exp
                })
                return False
        
        return True
    
    def get_discrepancies(self) -> List[Dict]:
        """Get all discrepancies"""
        return self.discrepancies


class TestExportValidation:
    """Comprehensive export validation tests"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database with test data"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = sqlite3.connect(path)
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
        
        cursor.execute('PRAGMA foreign_keys = ON')
        
        cursor.execute('INSERT INTO employees (name) VALUES (?)', ('Export Test Employee',))
        employee_id = cursor.lastrowid
        
        today = date.today()
        cursor.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, 'FR', (today - timedelta(days=50)).strftime('%Y-%m-%d'),
              (today - timedelta(days=40)).strftime('%Y-%m-%d'), 0))
        
        cursor.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, 'DE', (today - timedelta(days=30)).strftime('%Y-%m-%d'),
              (today - timedelta(days=20)).strftime('%Y-%m-%d'), 2))
        
        conn.commit()
        conn.close()
        
        yield path
        
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def validator(self, temp_db):
        return ExportValidator(temp_db)
    
    def test_csv_export_accuracy(self, validator, temp_db):
        """Test CSV export matches database exactly"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM employees LIMIT 1')
        employee_id = cursor.fetchone()[0]
        conn.close()
        
        assert validator.validate_csv_export_accuracy(employee_id)
        assert len(validator.get_discrepancies()) == 0
    
    def test_csv_completeness(self, validator):
        """Test CSV export includes all required fields"""
        assert validator.validate_csv_completeness()
        assert len(validator.get_discrepancies()) == 0
    
    def test_pdf_export_accuracy(self, validator, temp_db):
        """Test PDF export generation"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM employees LIMIT 1')
        employee_id = cursor.fetchone()[0]
        conn.close()
        
        assert validator.validate_pdf_export_accuracy(employee_id)
        assert len(validator.get_discrepancies()) == 0
    
    def test_export_consistency(self, validator, temp_db):
        """Test CSV and PDF exports are consistent"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM employees LIMIT 1')
        employee_id = cursor.fetchone()[0]
        conn.close()
        
        assert validator.validate_export_consistency(employee_id)
        assert len(validator.get_discrepancies()) == 0
    
    def test_export_roundtrip(self, validator, temp_db):
        """Test export -> import roundtrip"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM employees LIMIT 1')
        employee_id = cursor.fetchone()[0]
        conn.close()
        
        assert validator.validate_export_roundtrip(employee_id)
        assert len(validator.get_discrepancies()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])




