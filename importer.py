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

    upper_text = cell_text.upper()

    # Explicit UK markers
    if ' UK' in f" {upper_text} " or ' GB' in f" {upper_text} ":
        return 'UK'
    
    # Use regex to find 2-letter country codes as standalone words
    pattern = r'\b([A-Z]{2})\b'
    matches = re.findall(pattern, upper_text)
    
    for match in matches:
        if match in EU_COUNTRIES:
            return match
    
    # No country detected
    return None

def infer_country_from_context(row_cells: Tuple, tuple_index: int) -> Optional[str]:
    """
    Infer country by scanning neighboring cells in the same row.
    Looks left and right up to 7 columns for a non-UK country code.
    """
    if not row_cells or tuple_index is None:
        return None
    scan_offsets = [-1, -2, -3, -4, -5, -6, -7, 1, 2, 3, 4, 5, 6, 7]
    for delta in scan_offsets:
        idx = tuple_index + delta
        if idx < 0 or idx >= len(row_cells):
            continue
        neighbor_val = row_cells[idx]
        if not neighbor_val:
            continue
        neighbor_text = str(neighbor_val).strip()
        neighbor_country = detect_country_enhanced(neighbor_text)
        if neighbor_country and neighbor_country != 'UK':
            return neighbor_country
    return None

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

def find_date_headers(worksheet, max_rows: int = 50, enable_extended_scan: bool = True) -> Tuple[int, List[Tuple[int, date]]]:
    """
    Find the row containing date headers and extract dates with their column indices.
    Returns (header_row_index, list_of_(col_idx, date))
    
    OPTIMIZED: Focuses on the last 180 days from current date for rolling compliance tracking
    """
    from datetime import datetime, timedelta
    
    dates_with_cols: List[Tuple[int, date]] = []
    header_row = None

    # OPTIMIZED: Calculate the relevant date range (180 days back + reasonable future buffer)
    today = datetime.now().date()
    start_date = today - timedelta(days=180)
    # Include future dates up to 6 months ahead for planning and compliance forecasting
    end_date = today + timedelta(days=180)
    logger.info(f"Focusing on date range: {start_date} to {end_date} (180 days back + 180 days forward)")

    # Use actual worksheet dimensions but we'll filter dates later
    actual_max_col = getattr(worksheet, 'max_column', None)
    if actual_max_col:
        max_cols_to_scan = actual_max_col
        logger.info(f"Using actual worksheet dimensions: {actual_max_col} columns")
    else:
        # Fallback to a reasonable number for 180 days
        max_cols_to_scan = 200  # Should cover 180 days comfortably
        logger.info(f"Using fallback column limit: {max_cols_to_scan} columns")

    for row_idx in range(1, max_rows + 1):
        row_dates: List[Tuple[int, date]] = []
        # Stream row values for speed
        for cells in worksheet.iter_rows(min_row=row_idx, max_row=row_idx, min_col=2, max_col=max_cols_to_scan, values_only=True):
            for offset, value in enumerate(cells, start=0):
                if value:
                    parsed_date = parse_date_header(value)
                    if parsed_date:
                        # OPTIMIZED: Include dates within 180 days back + 180 days forward
                        if start_date <= parsed_date <= end_date:
                            col_idx = 2 + offset
                            row_dates.append((col_idx, parsed_date))
                        else:
                            # Log skipped dates for debugging
                            logger.debug(f"Skipping date {parsed_date} (outside 360-day range)")

        # Found a row with at least 3 dates
        if len(row_dates) >= 3:
            header_row = row_idx
            dates_with_cols = row_dates
            logger.info(f"Found date headers in row {header_row} with {len(dates_with_cols)} dates")
            logger.info(f"Date range: {min(dates_with_cols, key=lambda x: x[1])[1]} to {max(dates_with_cols, key=lambda x: x[1])[1]}")
            break

    if header_row is None:
        logger.warning("No date headers found in the first 15 rows")
    else:
        # Log the date range to help with debugging
        date_range = [d[1] for d in dates_with_cols]
        min_date = min(date_range)
        max_date = max(date_range)
        logger.info(f"Date header range: {min_date} to {max_date} ({len(dates_with_cols)} total dates)")
        
        # OPTIMIZED: Validation for 360-day window (180 back + 180 forward)
        if enable_extended_scan:
            date_span_days = (max_date - min_date).days
            if date_span_days < 60:  # Less than 2 months in the 360-day window
                logger.warning(f"Date range seems too narrow ({date_span_days} days). Trying extended scan...")
                # Try scanning more columns to find additional dates within the 360-day window
                extended_dates = find_extended_date_headers(worksheet, header_row, max_cols_to_scan, start_date, end_date)
                if extended_dates:
                    dates_with_cols.extend(extended_dates)
                    dates_with_cols.sort(key=lambda x: x[1])  # Sort by date
                    logger.info(f"Extended scan found {len(extended_dates)} additional dates within 360-day window")
                    logger.info(f"New date range: {min(dates_with_cols, key=lambda x: x[1])[1]} to {max(dates_with_cols, key=lambda x: x[1])[1]}")

    return header_row, dates_with_cols

def find_extended_date_headers(worksheet, header_row: int, max_cols_to_scan: int, start_date: date, end_date: date) -> List[Tuple[int, date]]:
    """
    Extended scan to find additional date headers within the 360-day window (180 back + 180 forward).
    This helps catch edge cases where dates are not consecutive.
    """
    extended_dates = []
    
    # Scan the same header row but with a wider column range
    for cells in worksheet.iter_rows(min_row=header_row, max_row=header_row, min_col=2, max_col=max_cols_to_scan, values_only=True):
        for offset, value in enumerate(cells, start=0):
            if value:
                parsed_date = parse_date_header(value)
                if parsed_date:
                    # Only include dates within the 360-day window (180 back + 180 forward)
                    if start_date <= parsed_date <= end_date:
                        col_idx = 2 + offset
                        extended_dates.append((col_idx, parsed_date))
    
    return extended_dates

def process_excel_file(file_path: str, enable_extended_scan: bool = True) -> Dict:
    """
    Process Excel file and return import summary.
    OPTIMIZED: Focuses on 180 days back + 180 days forward for rolling compliance tracking and planning.
    
    Args:
        file_path: Path to the Excel file to process
        enable_extended_scan: If True, enables extended column scanning to catch edge cases
    """
    try:
        # Load Excel file in read-only streaming mode for performance
        workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        worksheet = workbook.active
        
        logger.info(f"Excel file loaded. Shape: ({worksheet.max_row}, {worksheet.max_column})")
        
        # Find date headers with their actual column indices
        header_row, dates_with_cols = find_date_headers(worksheet, enable_extended_scan=enable_extended_scan)
        if not header_row:
            return {
                'success': False,
                'error': 'Could not find date headers in the first 15 rows'
            }
        
        logger.info(f"Detected header row at position: {header_row}")
        
        # Process employee rows
        trip_records = []
        employees_processed = 0
        
        # ENHANCED: Use actual worksheet dimensions to ensure we read all employee rows
        actual_max_row = getattr(worksheet, 'max_row', None)
        if actual_max_row:
            max_rows_to_scan = actual_max_row
            logger.info(f"Using actual worksheet dimensions: {actual_max_row} rows")
        else:
            # Fallback to a large number if max_row is not available
            max_rows_to_scan = header_row + 10000  # Should cover most employee lists
            logger.info(f"Using fallback row limit: {max_rows_to_scan} rows")
        
        consecutive_empty_names = 0

        # ENHANCED: Use the full column range instead of limiting to detected date columns
        # This ensures we don't miss any data in columns beyond the detected date range
        actual_max_col = getattr(worksheet, 'max_column', None)
        if actual_max_col:
            max_date_col = actual_max_col
            logger.info(f"Scanning all columns up to: {max_date_col}")
        else:
            # Fallback to detected date columns if we can't get actual dimensions
            max_date_col = max((c for c, _ in dates_with_cols), default=2)
            logger.info(f"Using detected date columns up to: {max_date_col}")

        for cells in worksheet.iter_rows(min_row=header_row + 1, max_row=max_rows_to_scan, min_col=1, max_col=max_date_col, values_only=True):
            # Column A (index 0) is employee name
            employee_val = cells[0] if cells and len(cells) > 0 else None
            if not employee_val or not str(employee_val).strip():
                consecutive_empty_names += 1
                # ENHANCED: More intelligent empty row detection
                # Only stop if we see a very long run of empty rows (increased from 50 to 200)
                # This prevents stopping too early on sheets with many empty rows
                if consecutive_empty_names >= 200:
                    logger.info(f"Stopping at row {header_row + 1 + employees_processed + consecutive_empty_names} after {consecutive_empty_names} consecutive empty rows")
                    break
                continue
            consecutive_empty_names = 0
            
            employee_name = str(employee_val).strip()
            
            # Skip "Unallocated" or similar sections
            if employee_name.lower() in ['unallocated', 'unassigned', '']:
                continue
            
            employees_processed += 1
            logger.info(f"Processing employee: {employee_name}")
            
            # Track travel days found for this employee for debugging
            employee_travel_days = []
            
            # Process each date column: read cell value from the streamed row tuple
            last_non_uk_country: Optional[str] = None
            for col_idx, trip_date in dates_with_cols:
                tuple_index = col_idx - 1  # cells is 0-based
                if tuple_index >= len(cells):
                    continue
                cell_value = cells[tuple_index]
                if not cell_value:
                    continue
                cell_text = str(cell_value).strip()
                country = detect_country_enhanced(cell_text)
                is_travel = is_travel_day(cell_text)

                # If no country detected but cell marks travel, infer from context
                if not country and is_travel:
                    # Prefer last seen non-UK country in row
                    if last_non_uk_country:
                        country = last_non_uk_country
                    else:
                        inferred = infer_country_from_context(cells, tuple_index)
                        if inferred:
                            country = inferred
                            logger.info(f"Inferred country {inferred} for {employee_name} on {trip_date} from neighboring cells")
                
                # Skip UK/domestic work
                if country == 'UK':
                    continue
                
                if country:
                    trip_records.append({
                        'employee': employee_name,
                        'date': trip_date,
                        'country': country,
                        'is_travel': is_travel,
                        'text': cell_text
                    })
                    
                    # Track travel days for debugging
                    if is_travel:
                        employee_travel_days.append(trip_date)
                    if country and country != 'UK':
                        last_non_uk_country = country
                    
                    # Avoid per-cell verbose logging for performance
                    # logger.debug(f"Found trip: {trip_date} - {country} - Travel: {is_travel}")
            
            # Log travel days found for this employee (helpful for debugging)
            if employee_travel_days:
                logger.info(f"  {employee_name}: Found {len(employee_travel_days)} travel days: {sorted(employee_travel_days)}")
        
        logger.info(f"Total trip records found: {len(trip_records)}")
        logger.info(f"Total employees processed: {employees_processed}")
        logger.info(f"Total rows scanned: {max_rows_to_scan - header_row}")
        logger.info(f"Total columns scanned: {max_date_col}")
        
        # Aggregate consecutive days into trip blocks
        aggregated_trips = aggregate_trips(trip_records)
        
        # Save to database
        save_result = save_trips_to_database(aggregated_trips)
        
        # ENHANCED: Provide comprehensive processing summary
        processing_summary = {
            'success': True,
            'trips_added': len(save_result.get('trips', [])),
            'employees_processed': employees_processed,
            'total_records': len(trip_records),
            'aggregated_trips': len(aggregated_trips),
            'trips': save_result.get('trips', []),
            'duplicates_skipped': save_result.get('duplicates_skipped', 0),
            'uk_jobs_skipped': save_result.get('uk_jobs_skipped', 0),
            'empty_cells_skipped': save_result.get('empty_cells_skipped', 0),
            # New comprehensive metrics
            'worksheet_dimensions': {
                'total_rows': max_rows_to_scan,
                'total_columns': max_date_col,
                'header_row': header_row,
                'rows_scanned': max_rows_to_scan - header_row
            },
            'date_coverage': {
                'dates_found': len(dates_with_cols),
                'date_range': f"{min(dates_with_cols, key=lambda x: x[1])[1]} to {max(dates_with_cols, key=lambda x: x[1])[1]}" if dates_with_cols else "No dates found"
            }
        }
        
        logger.info(f"Processing complete. Summary: {processing_summary['employees_processed']} employees, {processing_summary['trips_added']} trips added")
        logger.info(f"Focused on 180 days back + 180 days forward for rolling compliance tracking and planning")
        return processing_summary
        
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
                
                # logger.debug(f"Extend trip to {record['date']}, travel_day: {record['is_travel']}")
            else:
                # Complete current trip and start new one
                # logger.debug("Completed trip block")
                aggregated.append(current_trip)
                
                current_trip = {
                    'employee': record['employee'],
                    'country': record['country'],
                    'entry_date': record['date'],
                    'exit_date': record['date'],
                    'travel_days': 1 if record['is_travel'] else 0,
                    'total_days': 1
                }
                # logger.debug("Start new trip block")
    
    # Add final trip
    if current_trip:
        # logger.debug("Completed final trip block")
        aggregated.append(current_trip)
    
    logger.info(f"After aggregation: {len(aggregated)} trip blocks")
    return aggregated

def save_trips_to_database(trips: List[Dict]) -> List[Dict]:
    """
    Save trips to SQLite database with duplicate prevention.
    """
    if not trips:
        return []
    
    # Prefer the Flask-configured database if available
    db_path = None
    try:
        from flask import current_app
        if current_app and current_app.config.get('DATABASE'):
            db_path = current_app.config['DATABASE']
    except Exception:
        # Not in an application context
        pass

    if not db_path:
        # Fallback to local paths
        candidate = os.path.join(os.path.dirname(__file__), 'eu_tracker.db')
        db_path = candidate if os.path.exists(candidate) else os.path.join(os.path.dirname(__file__), 'data', 'eu_tracker.db')
    
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

def import_excel(file_path: str, enable_extended_scan: bool = True) -> Dict:
    """
    Main function to import Excel file and return results.
    
    Args:
        file_path: Path to the Excel file to process
        enable_extended_scan: If True, enables extended column scanning to catch edge cases
    """
    return process_excel_file(file_path, enable_extended_scan)
