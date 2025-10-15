"""
Enhanced Excel Import System for EU 90/180 Tracker

This module handles importing trip data from Excel files with automatic
country detection, travel day identification, and trip aggregation.
"""

import openpyxl
import re
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)

# EU/Schengen country codes
EU_COUNTRIES = {
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'ES', 'FI', 'FR', 'DE', 
    'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU', 'MT', 'NL', 'NO', 
    'PL', 'PT', 'RO', 'SK', 'SI', 'SE', 'CH'
}

def detect_country_enhanced(cell_text: str) -> Optional[str]:
    """
    Enhanced country detection using regex pattern matching.
    Finds any 2-letter uppercase code in the cell text.
    """
    if not cell_text or not isinstance(cell_text, str):
        return None
    
    # Use regex to find 2-letter country codes as standalone words
    pattern = r'\b([A-Z]{2})\b'
    matches = re.findall(pattern, cell_text.upper())
    
    for match in matches:
        if match in EU_COUNTRIES:
            return match
    
    # Default to UK for domestic work (will be ignored in trip calculations)
    return 'UK'

def is_travel_day(cell_text: str) -> bool:
    """
    Check if a cell represents a travel day.
    Travel days are marked with 'tr' or 'tr/' prefix.
    """
    if not cell_text or not isinstance(cell_text, str):
        return False
    
    return cell_text.lower().startswith(('tr', 'tr/'))

def parse_date_header(date_str: str) -> Optional[date]:
    """
    Parse various date formats from Excel headers.
    Supports: 'Mon 29 Sep', '29/09/2024', '29-09-2024', datetime objects
    """
    if not date_str:
        return None
    
    # Handle datetime objects
    if isinstance(date_str, datetime):
        return date_str.date()
    
    if isinstance(date_str, date):
        return date_str
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    formats = [
        '%d/%m/%Y',      # 29/09/2024
        '%d-%m-%Y',      # 29-09-2024
        '%Y-%m-%d',      # 2024-09-29
        '%d %b %Y',      # 29 Sep 2024
        '%a %d %b',      # Mon 29 Sep
        '%d/%m/%y',      # 29/09/24
        '%d-%m-%y',      # 29-09-24
        '%a %d %b %Y',   # Mon 29 Sep 2024
        '%d %b',         # 29 Sep (current year)
        '%a %d %b %Y',   # Mon 15 Jan 2024
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # Handle year-less formats by assuming current year
            if fmt in ['%a %d %b', '%d %b']:
                current_year = datetime.now().year
                parsed_date = parsed_date.replace(year=current_year)
            return parsed_date
        except ValueError:
            continue
    
    # Try to extract date from strings like "Mon 15 Jan" by parsing manually
    try:
        parts = date_str.split()
        if len(parts) >= 3:
            # Look for day number
            for part in parts:
                if part.isdigit() and 1 <= int(part) <= 31:
                    day = int(part)
                    # Look for month name
                    month_names = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    for part2 in parts:
                        if part2.lower() in month_names:
                            month = month_names[part2.lower()]
                            current_year = datetime.now().year
                            return date(current_year, month, day)
    except:
        pass
    
    return None

def find_date_headers(worksheet, max_rows: int = 15) -> Tuple[int, List[date]]:
    """
    Find the row containing date headers and extract dates.
    Returns (header_row_index, list_of_dates)
    """
    dates = []
    header_row = None
    
    for row_idx in range(1, max_rows + 1):
        row_dates = []
        for col_idx in range(2, worksheet.max_column + 1):  # Start from column B
            cell = worksheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                parsed_date = parse_date_header(cell.value)
                if parsed_date:
                    row_dates.append(parsed_date)
        
        if len(row_dates) >= 3:  # Found a row with at least 3 dates
            header_row = row_idx
            dates = row_dates
            break
    
    return header_row, dates

def process_excel_file(file_path: str) -> Dict:
    """
    Process Excel file and return import summary.
    """
    try:
        # Load Excel file
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        worksheet = workbook.active
        
        logger.info(f"Excel file loaded. Shape: ({worksheet.max_row}, {worksheet.max_column})")
        
        # Find date headers
        header_row, dates = find_date_headers(worksheet)
        if not header_row:
            return {
                'success': False,
                'error': 'Could not find date headers in the first 15 rows'
            }
        
        logger.info(f"Detected header row at position: {header_row}")
        
        # Process employee rows
        trip_records = []
        employees_processed = 0
        
        for row_idx in range(header_row + 1, worksheet.max_row + 1):
            # Get employee name from column A
            employee_cell = worksheet.cell(row=row_idx, column=1)
            if not employee_cell.value or not str(employee_cell.value).strip():
                continue
            
            employee_name = str(employee_cell.value).strip()
            
            # Skip "Unallocated" or similar sections
            if employee_name.lower() in ['unallocated', 'unassigned', '']:
                continue
            
            employees_processed += 1
            logger.info(f"Processing employee: {employee_name}")
            
            # Process each date column
            for col_idx, trip_date in enumerate(dates, start=2):
                if col_idx > worksheet.max_column:
                    break
                
                cell = worksheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                country = detect_country_enhanced(cell_text)
                
                # Skip UK/domestic work
                if country == 'UK':
                    continue
                
                if country:
                    is_travel = is_travel_day(cell_text)
                    trip_records.append({
                        'employee': employee_name,
                        'date': trip_date,
                        'country': country,
                        'is_travel': is_travel,
                        'text': cell_text
                    })
                    
                    logger.info(f"  Found trip: {trip_date} - {country} - Travel: {is_travel} - Text: '{cell_text}'")
        
        logger.info(f"Total trip records found: {len(trip_records)}")
        
        # Aggregate consecutive days into trip blocks
        aggregated_trips = aggregate_trips(trip_records)
        
        # Save to database
        saved_trips = save_trips_to_database(aggregated_trips)
        
        return {
            'success': True,
            'trips_added': len(saved_trips),
            'employees_processed': employees_processed,
            'total_records': len(trip_records),
            'aggregated_trips': len(aggregated_trips),
            'trips': saved_trips
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def aggregate_trips(trip_records: List[Dict]) -> List[Dict]:
    """
    Aggregate consecutive days into trip blocks.
    """
    if not trip_records:
        return []
    
    # Sort by employee, then by date
    trip_records.sort(key=lambda x: (x['employee'], x['date']))
    
    logger.info(f"Starting aggregation with {len(trip_records)} records...")
    
    aggregated = []
    current_trip = None
    
    for record in trip_records:
        if not current_trip:
            # Start new trip
            current_trip = {
                'employee': record['employee'],
                'country': record['country'],
                'entry_date': record['date'],
                'exit_date': record['date'],
                'travel_days': 1 if record['is_travel'] else 0,
                'total_days': 1
            }
            logger.info(f"  Started new trip: {record['employee']} to {record['country']} starting {record['date']}")
        else:
            # Check if we can extend current trip
            if (current_trip['employee'] == record['employee'] and 
                current_trip['country'] == record['country'] and
                (record['date'] - current_trip['exit_date']).days <= 1):
                
                # Extend trip
                current_trip['exit_date'] = record['date']
                current_trip['total_days'] += 1
                if record['is_travel']:
                    current_trip['travel_days'] += 1
                
                logger.info(f"    Extended trip to {record['date']}, travel_day: {record['is_travel']}")
            else:
                # Complete current trip and start new one
                logger.info(f"  Completed trip: {current_trip['employee']} to {current_trip['country']} from {current_trip['entry_date']} to {current_trip['exit_date']} ({current_trip['travel_days']} travel days)")
                aggregated.append(current_trip)
                
                current_trip = {
                    'employee': record['employee'],
                    'country': record['country'],
                    'entry_date': record['date'],
                    'exit_date': record['date'],
                    'travel_days': 1 if record['is_travel'] else 0,
                    'total_days': 1
                }
                logger.info(f"  Started new trip: {record['employee']} to {record['country']} starting {record['date']}")
    
    # Add final trip
    if current_trip:
        logger.info(f"  Completed trip: {current_trip['employee']} to {current_trip['country']} from {current_trip['entry_date']} to {current_trip['exit_date']} ({current_trip['travel_days']} travel days)")
        aggregated.append(current_trip)
    
    logger.info(f"After aggregation: {len(aggregated)} trip blocks")
    return aggregated

def save_trips_to_database(trips: List[Dict]) -> List[Dict]:
    """
    Save trips to SQLite database with duplicate prevention.
    """
    if not trips:
        return []
    
    # Get database path from environment or use default
    db_path = os.path.join(os.path.dirname(__file__), 'eu_tracker.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'eu_tracker.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    saved_trips = []
    duplicates_skipped = 0
    uk_jobs_skipped = 0
    empty_cells_skipped = 0
    
    try:
        for trip in trips:
            # Skip UK jobs
            if trip['country'] == 'UK':
                uk_jobs_skipped += 1
                continue
            
            # Get or create employee
            cursor.execute('SELECT id FROM employees WHERE name = ?', (trip['employee'],))
            employee = cursor.fetchone()
            
            if not employee:
                cursor.execute('INSERT INTO employees (name) VALUES (?)', (trip['employee'],))
                employee_id = cursor.lastrowid
            else:
                employee_id = employee['id']
            
            # Check for duplicate trip
            cursor.execute('''
                SELECT id FROM trips 
                WHERE employee_id = ? AND country = ? AND entry_date = ? AND exit_date = ?
            ''', (employee_id, trip['country'], trip['entry_date'], trip['exit_date']))
            
            if cursor.fetchone():
                duplicates_skipped += 1
                continue
            
            # Insert trip
            cursor.execute('''
                INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, trip['country'], trip['entry_date'], trip['exit_date'], trip['travel_days']))
            
            trip_id = cursor.lastrowid
            
            saved_trip = {
                'id': trip_id,
                'employee': trip['employee'],
                'country': trip['country'],
                'entry_date': trip['entry_date'].strftime('%Y-%m-%d'),
                'exit_date': trip['exit_date'].strftime('%Y-%m-%d'),
                'travel_days': trip['travel_days'],
                'total_days': trip['total_days']
            }
            
            saved_trips.append(saved_trip)
            logger.info(f"Saved trip: {trip['employee']} - {trip['country']} - {trip['entry_date']} to {trip['exit_date']} ({trip['travel_days']} travel days)")
        
        conn.commit()
        
        return {
            'trips': saved_trips,
            'duplicates_skipped': duplicates_skipped,
            'uk_jobs_skipped': uk_jobs_skipped,
            'empty_cells_skipped': empty_cells_skipped
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving trips to database: {e}")
        raise
    finally:
        conn.close()

def import_excel(file_path: str) -> Dict:
    """
    Main function to import Excel file and return results.
    """
    return process_excel_file(file_path)
