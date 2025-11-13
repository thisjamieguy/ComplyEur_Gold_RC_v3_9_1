"""
Excel Import Module for ComplyEur
Processes Excel files containing employee travel data and imports trips into the database.
"""

import re
import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import openpyxl
from openpyxl.utils import get_column_letter

# Schengen country codes
SCHENGEN_COUNTRIES = [
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'ES', 'FI', 'FR', 'DE',
    'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU', 'MT', 'NL', 'NO',
    'PL', 'PT', 'RO', 'SK', 'SI', 'SE', 'CH'
]


def detect_country_enhanced(cell_text: str) -> Optional[str]:
    """
    Enhanced country detection using regex to find any 2-letter uppercase code.
    Returns country code if found, 'UK' for domestic, or None if no valid country.
    """
    if not cell_text or not isinstance(cell_text, str):
        return 'UK'
    
    # Remove travel prefix for country detection
    text = cell_text.strip()
    if text.lower().startswith(('tr/', 'tr-')):
        text = text[3:].strip()
    elif text.lower().startswith('tr'):
        text = text[2:].strip()
    
    # Find any 2-letter uppercase code as a standalone word
    pattern = r'\b([A-Z]{2})\b'
    matches = re.findall(pattern, text)
    
    for match in matches:
        if match in SCHENGEN_COUNTRIES:
            return match
    
    # Default to UK for domestic work
    return 'UK'


def is_travel_day(cell_text: str) -> bool:
    """
    Check if cell text indicates a travel day (starts with 'tr' or 'tr/').
    Case insensitive.
    """
    if not cell_text or not isinstance(cell_text, str):
        return False
    
    text = cell_text.strip().lower()
    return text.startswith(('tr/', 'tr-')) or (text.startswith('tr') and len(text) > 2 and text[2] in [' ', '/', '-'])


def parse_date_header(cell_value: Any) -> Optional[date]:
    """
    Parse date from various Excel header formats.
    Supports: "Mon 29 Sep", "29/09/2024", "29-09-2024", datetime objects.
    """
    if not cell_value:
        return None
    
    # If it's already a date/datetime object
    if isinstance(cell_value, (date, datetime)):
        if isinstance(cell_value, datetime):
            return cell_value.date()
        return cell_value
    
    # Convert to string
    cell_str = str(cell_value).strip()
    if not cell_str:
        return None
    
    # Try various date formats
    date_formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y-%m-%d',
        '%d/%m/%y',
        '%d-%m-%y',
        '%Y/%m/%d',
        '%d %b %Y',  # "29 Sep 2024"
        '%d %B %Y',  # "29 September 2024"
        '%a %d %b',  # "Mon 29 Sep"
        '%A %d %B',  # "Monday 29 September"
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(cell_str, fmt)
            # For formats without year, assume current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.date()
        except ValueError:
            continue
    
    return None


def find_header_row(ws, max_rows: int = 15) -> Optional[int]:
    """
    Scan first max_rows to find the header row containing dates.
    Returns row number (1-indexed) or None if not found.
    """
    for row_idx in range(1, min(max_rows + 1, ws.max_row + 1)):
        date_count = 0
        for col_idx in range(2, min(ws.max_column + 1, 100)):  # Check up to column 100
            cell_value = ws.cell(row=row_idx, column=col_idx).value
            if parse_date_header(cell_value):
                date_count += 1
                if date_count >= 3:  # Found at least 3 dates, likely the header row
                    return row_idx
    return None


def get_database_path() -> str:
    """
    Get database path from environment or default location.
    Works both in Flask app context and standalone.
    """
    # Try Flask app context first
    try:
        from flask import has_app_context, current_app
        if has_app_context() and current_app:
            db_path = current_app.config.get('DATABASE')
            if db_path:
                # Ensure path is absolute
                if not os.path.isabs(db_path):
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
                    db_path = os.path.join(project_root, db_path)
                return os.path.abspath(db_path)
    except (RuntimeError, ImportError, AttributeError) as e:
        # Log but continue to fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not get database path from Flask app context: {e}")
    
    # Fall back to environment variable
    db_path = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
    
    # Make absolute if relative
    if not os.path.isabs(db_path):
        project_root = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(project_root, db_path)
    
    return os.path.abspath(db_path)


def get_or_create_employee(conn: sqlite3.Connection, name: str) -> int:
    """
    Get existing employee ID or create new employee.
    Returns employee ID.
    """
    c = conn.cursor()
    
    # Try to find existing employee
    c.execute('SELECT id FROM employees WHERE name = ?', (name,))
    row = c.fetchone()
    if row:
        return row[0]
    
    # Create new employee
    c.execute('INSERT INTO employees (name) VALUES (?)', (name,))
    conn.commit()
    return c.lastrowid


def trip_exists(conn: sqlite3.Connection, employee_id: int, country: str, entry_date: date, exit_date: date) -> bool:
    """
    Check if a trip with the same employee, country, and dates already exists.
    """
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM trips
        WHERE employee_id = ? AND country = ? AND entry_date = ? AND exit_date = ?
    ''', (employee_id, country, entry_date.isoformat(), exit_date.isoformat()))
    return c.fetchone()[0] > 0


def save_trip(conn: sqlite3.Connection, employee_id: int, country: str, entry_date: date, 
               exit_date: date, travel_days: int) -> bool:
    """
    Save a trip to the database if it doesn't already exist.
    Returns True if saved, False if duplicate.
    """
    if trip_exists(conn, employee_id, country, entry_date, exit_date):
        return False
    
    c = conn.cursor()
    c.execute('''
        INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days)
        VALUES (?, ?, ?, ?, ?)
    ''', (employee_id, country, entry_date.isoformat(), exit_date.isoformat(), travel_days))
    conn.commit()
    return True


def import_excel(file_path: str, enable_extended_scan: bool = False) -> Dict[str, Any]:
    """
    Import trips from an Excel file.
    
    Args:
        file_path: Path to the Excel file (.xlsx or .xls)
        enable_extended_scan: If True, scans more rows for headers (default: False)
    
    Returns:
        Dictionary with keys:
        - success: bool
        - trips_added: int
        - employees_processed: int
        - employees_created: int
        - total_employee_names_found: int
        - aggregated_trips: int
        - total_records: int
        - error: str (if success is False)
    """
    try:
        # Load workbook
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        # Find header row
        max_scan_rows = 20 if enable_extended_scan else 15
        header_row = find_header_row(ws, max_scan_rows)
        
        if not header_row:
            return {
                'success': False,
                'error': 'Could not find date header row in first 15 rows'
            }
        
        # Extract date columns
        date_columns = {}  # {col_idx: date}
        for col_idx in range(2, ws.max_column + 1):
            cell_value = ws.cell(row=header_row, column=col_idx).value
            parsed_date = parse_date_header(cell_value)
            if parsed_date:
                date_columns[col_idx] = parsed_date
        
        if not date_columns:
            return {
                'success': False,
                'error': 'No valid date columns found in header row'
            }
        
        # Process employee rows
        records = []  # List of (employee_name, date, country, is_travel)
        employee_names = set()
        
        for row_idx in range(header_row + 1, ws.max_row + 1):
            # Get employee name from column A
            employee_name = ws.cell(row=row_idx, column=1).value
            if not employee_name or not isinstance(employee_name, str):
                continue
            
            employee_name = employee_name.strip()
            if not employee_name or employee_name.lower() == 'unallocated':
                continue
            
            employee_names.add(employee_name)
            
            # Process each date column
            for col_idx, cell_date in date_columns.items():
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if not cell_value:
                    continue
                
                cell_text = str(cell_value).strip()
                if not cell_text:
                    continue
                
                country = detect_country_enhanced(cell_text)
                if country == 'UK':
                    continue  # Skip domestic work
                
                is_travel = is_travel_day(cell_text)
                records.append((employee_name, cell_date, country, is_travel))
        
        if not records:
            return {
                'success': False,
                'error': 'No valid trip records found in Excel file'
            }
        
        # Aggregate consecutive days into trips
        trips = []  # List of (employee_name, country, entry_date, exit_date, travel_days)
        
        # Sort records by employee, then date
        records.sort(key=lambda x: (x[0], x[1]))
        
        current_trip = None  # (employee_name, country, entry_date, last_date, travel_days)
        
        for employee_name, trip_date, country, is_travel in records:
            if current_trip is None:
                # Start new trip
                current_trip = (employee_name, country, trip_date, trip_date, 1 if is_travel else 0)
            elif (current_trip[0] == employee_name and 
                  current_trip[1] == country and 
                  (trip_date - current_trip[3]).days <= 1):
                # Extend current trip
                travel_days = current_trip[4] + (1 if is_travel else 0)
                current_trip = (current_trip[0], current_trip[1], current_trip[2], trip_date, travel_days)
            else:
                # Save current trip and start new one
                trips.append((current_trip[0], current_trip[1], current_trip[2], current_trip[3], current_trip[4]))
                current_trip = (employee_name, country, trip_date, trip_date, 1 if is_travel else 0)
        
        # Don't forget the last trip
        if current_trip:
            trips.append((current_trip[0], current_trip[1], current_trip[2], current_trip[3], current_trip[4]))
        
        # Connect to database and save trips
        db_path = get_database_path()
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        trips_added = 0
        employees_created = 0
        employees_processed = set()
        
        for employee_name, country, entry_date, exit_date, travel_days in trips:
            employee_id = get_or_create_employee(conn, employee_name)
            if employee_id not in employees_processed:
                # Check if this is a new employee
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM employees WHERE id = ? AND created_at > datetime("now", "-1 minute")', (employee_id,))
                if c.fetchone()[0] > 0:
                    employees_created += 1
                employees_processed.add(employee_id)
            
            if save_trip(conn, employee_id, country, entry_date, exit_date, travel_days):
                trips_added += 1
        
        conn.close()
        
        return {
            'success': True,
            'trips_added': trips_added,
            'employees_processed': len(employees_processed),
            'employees_created': employees_created,
            'total_employee_names_found': len(employee_names),
            'aggregated_trips': len(trips),
            'total_records': len(records)
        }
    
    except FileNotFoundError:
        return {
            'success': False,
            'error': f'Excel file not found: {file_path}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing Excel file: {str(e)}'
        }


# Alias for backward compatibility
process_excel_file = import_excel

