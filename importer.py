import pandas as pd
import re
from datetime import datetime, timedelta
import openpyxl

# EU/Schengen country codes for 90-day rule tracking
SCHENGEN_CODES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "ES", "FI", "FR",
    "DE", "GR", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT",
    "NL", "NO", "PL", "PT", "RO", "SK", "SI", "SE", "CH"
}

def import_excel(file_path, db_path: str = 'eu_tracker.db'):
    """
    Import Excel file and extract trip data with enhanced detection logic.
    Automatically detects header row position and handles variable Excel formats.

    Expected format:
    - Column A: Employee names
    - Columns B+: Date columns with job descriptions
    - Data may start after "Unallocated" section (first 10+ rows)
    """
    try:
        # First, try to detect the correct header row by looking for date patterns
        header_row = detect_header_row(file_path)
        print(f"Detected header row at position: {header_row}")

        # Read Excel file with detected header row
        df = pd.read_excel(file_path, header=header_row)
        trip_records = []

        print(f"Excel file loaded. Shape: {df.shape}")
        print(f"Columns: {list(df.columns[:5])}...")  # Show first 5 column names

        # Process each row
        for row_idx, row in df.iterrows():
            employee = row.iloc[0]  # First column contains employee names

            # Skip empty rows or "Unallocated" entries
            if pd.isna(employee) or str(employee).strip().lower() in ['', 'none', 'unallocated', 'nan']:
                continue

            employee_name = str(employee).strip()
            print(f"Processing employee: {employee_name}")

            # Process each date column (starting from column 1)
            for col_idx in range(1, len(row)):
                cell_value = row.iloc[col_idx]
                if pd.isna(cell_value):
                    continue

                text = str(cell_value).strip()
                # Skip common empty/holiday values
                if text.lower() in ['', 'none', 'n/a', 'n/w', 'hol', 'holiday', 'off', '-']:
                    continue

                # Get the date from the column header
                date_header = df.columns[col_idx]
                parsed_date = parse_date_header(date_header)

                if not parsed_date:
                    continue  # Skip non-date columns

                # Detect country code in the text (any 2-letter code that matches Schengen)
                country = detect_country_enhanced(text)

                # Detect travel day (starts with "tr" or "tr/")
                travel_day = text.lower().startswith(("tr", "tr/"))

                # Only process if it's a foreign country (not UK)
                if country != "UK":
                    trip_records.append({
                        "employee": employee_name,
                        "date": parsed_date,
                        "country": country,
                        "travel_day": travel_day,
                        "text": text,
                        "row": row_idx + header_row + 1,  # Adjust for header offset
                        "col": col_idx + 1
                    })
                    print(f"  Found trip: {parsed_date} - {country} - Travel: {travel_day} - Text: '{text}'")

        print(f"Total trip records found: {len(trip_records)}")

        # Aggregate consecutive days into trip blocks
        aggregated_trips = aggregate_trips_enhanced(trip_records)
        print(f"After aggregation: {len(aggregated_trips)} trip blocks")

        # Save trips to database
        saved_trips = []
        for trip in aggregated_trips:
            try:
                emp_id = find_or_create_employee(trip["employee"], db_path=db_path)
                trip_id = save_trip(
                    emp_id,
                    trip["country"],
                    trip["entry_date"],
                    trip["exit_date"],
                    trip.get("travel_days", 0),
                    db_path=db_path
                )
                if trip_id:  # Only add if trip was saved (not duplicate)
                    saved_trips.append({
                        "id": trip_id,
                        "employee": trip["employee"],
                        "country": trip["country"],
                        "entry_date": trip["entry_date"],
                        "exit_date": trip["exit_date"],
                        "travel_days": trip.get("travel_days", 0),
                        "total_days": (trip["exit_date"] - trip["entry_date"]).days + 1
                    })
                    print(f"Saved trip: {trip['employee']} - {trip['country']} - {trip['entry_date']} to {trip['exit_date']} ({trip.get('travel_days', 0)} travel days)")
            except Exception as e:
                print(f"Error saving trip: {e}")

        return saved_trips

    except Exception as e:
        print(f"Error importing Excel file: {e}")
        raise

def detect_country_enhanced(text):
    """
    Country detection per schedule spec:
    - Consider ONLY the second hyphen-separated token as the country code
      (after an optional leading "tr/" prefix).
    - Example: "tr/Axc-BE-GSD" → tokens ["Axc", "BE", "GSD"] → country BE
               "Axc-BE-GSD" → tokens ["Axc", "BE", "GSD"] → country BE
               "Catalent-Swindon" → tokens ["Catalent", "Swindon"] → UK (ignore)
               "tr" or blank → UK
    - Return the 2-letter code if it’s a known Schengen code; otherwise "UK".
    """
    if not text:
        return "UK"

    raw = str(text).strip()
    if raw.lower() == 'tr':
        return "UK"  # travel back/standalone travel day has no destination

    # Strip leading travel prefix like "tr/" or "tr -"
    cleaned = re.sub(r'^\s*tr\s*/\s*', '', raw, flags=re.IGNORECASE)

    # Split on hyphens
    parts = [p.strip() for p in cleaned.split('-') if p is not None]

    # Need at least two tokens to have a candidate country at index 1
    if len(parts) < 2:
        return "UK"

    # If first token indicates office/admin, ignore as UK
    first_token = parts[0].upper()
    if first_token in {"OFFICE", "ADMIN", "WFO"} or "OFFICE" in first_token:
        return "UK"

    candidate = parts[1].upper()

    # Exactly two letters and in our Schengen set
    if re.fullmatch(r'[A-Z]{2}', candidate) and candidate in SCHENGEN_CODES:
        return candidate

    # Legacy special-case mapping retained
    if raw.strip().upper() == 'SPTS':
        return 'PT'

    return "UK"

def detect_country(text):
    """
    Legacy function - kept for backward compatibility
    """
    return detect_country_enhanced(text)

def detect_header_row(file_path):
    """
    Automatically detect which row contains the date headers.
    Looks for patterns like "Mon 29 Sep", date objects, or similar date formats.
    Returns the row index to use as header (0-based).
    """
    try:
        # Read first 15 rows to find date patterns
        df_sample = pd.read_excel(file_path, nrows=15, header=None)

        def is_weekday_token(s: str) -> bool:
            return bool(re.search(r'\b(mon|tue|wed|thu|fri|sat|sun)\b', s.lower()))

        def is_numeric_date_token(s: str) -> bool:
            # Matches formats like '29 Sep', '29-Sep', '29/09', '2024-09-29'
            return (
                bool(re.search(r'\b\d{1,2}[\s-](jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', s.lower())) or
                bool(re.search(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', s)) or
                bool(re.search(r'\b\d{4}-\d{2}-\d{2}\b', s))
            )

        candidate_day_row = None

        for row_idx in range(len(df_sample)):
            row = df_sample.iloc[row_idx]
            weekday_count = 0
            numeric_date_count = 0

            for cell in row.iloc[1:]:  # Skip first column (employee names)
                if pd.isna(cell):
                    continue
                if isinstance(cell, datetime):
                    numeric_date_count += 1
                    continue
                cell_str = str(cell).strip()
                if is_weekday_token(cell_str):
                    weekday_count += 1
                if is_numeric_date_token(cell_str):
                    numeric_date_count += 1

            # Prefer the row with actual numeric-like dates
            if numeric_date_count >= 5:
                print(f"Found date header row at index {row_idx} with {numeric_date_count} date columns")
                return row_idx

            # Remember weekday header row; we might pick the next row instead
            if weekday_count >= 5:
                candidate_day_row = row_idx

        # If we saw a weekday row, try using the next row as dates
        if candidate_day_row is not None and candidate_day_row + 1 < len(df_sample):
            print(f"Using row {candidate_day_row + 1} as date header (after weekday row {candidate_day_row})")
            return candidate_day_row + 1

        # Fallback: assume row 2 (index 2)
        print("Could not detect header row automatically, using default row 2")
        return 2

    except Exception as e:
        print(f"Error detecting header row: {e}")
        return 2  # Default fallback

def parse_date_header(date_header):
    """
    Parse various date header formats into a datetime.date object.
    Handles: datetime objects, "Mon 29 Sep", "29/09", etc.
    """
    try:
        # If it's already a datetime object
        if isinstance(date_header, datetime):
            return date_header.date()

        # Try to parse string date formats
        date_str = str(date_header).strip()

        # Skip obvious non-date columns
        if date_str.lower() in ['unnamed', 'nan', 'none', ''] or 'unnamed' in date_str.lower():
            return None

        # Try common date formats
        date_formats = [
            '%a %d %b',      # "Mon 29 Sep"
            '%d-%b',         # "29-Sep"
            '%d %b %Y',      # "29 Sep 2024"
            '%d/%m/%Y',      # "29/09/2024"
            '%d/%m',         # "29/09"
            '%d-%m-%Y',      # "29-09-2024"
            '%Y-%m-%d',      # "2024-09-29"
            '%d-%b-%Y',      # "29-Sep-2024"
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # If year is missing, assume current year
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                return parsed_date.date()
            except ValueError:
                continue

        # Try pandas date parsing as last resort
        try:
            parsed_date = pd.to_datetime(date_str)
            if not pd.isna(parsed_date):
                return parsed_date.date()
        except:
            pass

        return None

    except Exception as e:
        print(f"Error parsing date header '{date_header}': {e}")
        return None

def aggregate_trips_enhanced(records):
    """
    Enhanced trip aggregation: Combine consecutive foreign days (same employee, same country) into trip blocks.
    Handles travel days properly and provides detailed logging.
    """
    if not records:
        return []

    # Sort records by employee, then by date
    records.sort(key=lambda x: (x["employee"], x["date"]))

    trips = []
    current_trip = None

    print(f"Starting aggregation with {len(records)} records...")

    for record in records:
        # Skip UK entries (should already be filtered, but double-check)
        if record["country"] == "UK":
            continue

        # Determine if this starts a new trip
        start_new_trip = (
            not current_trip or  # No current trip
            record["employee"] != current_trip["employee"] or  # Different employee
            record["country"] != current_trip["country"] or  # Different country
            (record["date"] - current_trip["exit_date"]).days > 1  # Date gap > 1 day
        )

        if start_new_trip:
            # Save previous trip if exists
            if current_trip:
                trips.append(current_trip)
                print(f"  Completed trip: {current_trip['employee']} to {current_trip['country']} from {current_trip['entry_date']} to {current_trip['exit_date']} ({current_trip['travel_days']} travel days)")

            # Start new trip
            current_trip = {
                "employee": record["employee"],
                "country": record["country"],
                "entry_date": record["date"],
                "exit_date": record["date"],
                "travel_days": 1 if record["travel_day"] else 0
            }
            print(f"  Started new trip: {record['employee']} to {record['country']} starting {record['date']}")
        else:
            # Extend current trip
            current_trip["exit_date"] = record["date"]
            if record["travel_day"]:
                current_trip["travel_days"] += 1
            print(f"    Extended trip to {record['date']}, travel_day: {record['travel_day']}")

    # Add final trip
    if current_trip:
        trips.append(current_trip)
        print(f"  Final trip: {current_trip['employee']} to {current_trip['country']} from {current_trip['entry_date']} to {current_trip['exit_date']} ({current_trip['travel_days']} travel days)")

    return trips

def aggregate_trips(records):
    """
    Legacy function - kept for backward compatibility
    """
    return aggregate_trips_enhanced(records)

def find_or_create_employee(name, db_path: str = 'eu_tracker.db'):
    """
    Find or create employee by name.
    Returns employee ID.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Try to find existing employee
    c.execute('SELECT id FROM employees WHERE name = ?', (name,))
    result = c.fetchone()
    
    if result:
        employee_id = result[0]
    else:
        # Create new employee
        c.execute('INSERT INTO employees (name) VALUES (?)', (name,))
        employee_id = c.lastrowid
        print(f"Created new employee: {name} (ID: {employee_id})")
    
    conn.commit()
    conn.close()
    
    return employee_id

def save_trip(employee_id, country, entry_date, exit_date, travel_days=0, db_path: str = 'eu_tracker.db'):
    """
    Save trip to database.
    Returns trip ID.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Convert dates to string format
    entry_date_str = entry_date.strftime('%Y-%m-%d')
    exit_date_str = exit_date.strftime('%Y-%m-%d')
    
    # Check if trip already exists
    c.execute('SELECT id FROM trips WHERE employee_id = ? AND entry_date = ? AND exit_date = ?',
              (employee_id, entry_date_str, exit_date_str))
    
    if c.fetchone():
        print(f"Trip already exists for employee {employee_id}: {entry_date_str} to {exit_date_str}")
        conn.close()
        return None
    
    # Insert new trip
    c.execute('''
        INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days) 
        VALUES (?, ?, ?, ?, ?)
    ''', (employee_id, country, entry_date_str, exit_date_str, travel_days))
    
    trip_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return trip_id

def process_excel(file_path: str, db_path: str) -> dict:
    """
    Reads the Excel file, detects EU country codes, aggregates consecutive days into trips,
    saves to SQLite, and returns a summary dict.

    Summary keys:
    - trips_added: int
    - duplicates_skipped: int
    - uk_jobs_skipped: int
    - empty_cells_skipped: int
    - errors: list[str]
    - trips: list[dict] (only trips that were added)
    - source_file: str
    """
    summary = {
        "trips_added": 0,
        "duplicates_skipped": 0,
        "uk_jobs_skipped": 0,
        "empty_cells_skipped": 0,
        "errors": [],
        "trips": [],
        "source_file": file_path
    }

    try:
        header_row = detect_header_row(file_path)
        df = pd.read_excel(file_path, header=header_row)

        trip_records = []

        for row_idx, row in df.iterrows():
            employee = row.iloc[0]
            if pd.isna(employee) or str(employee).strip().lower() in ['', 'none', 'unallocated', 'nan']:
                continue
            employee_name = str(employee).strip()

            for col_idx in range(1, len(row)):
                cell_value = row.iloc[col_idx]
                if pd.isna(cell_value):
                    continue

                text = str(cell_value).strip()
                if text.lower() in ['', 'none', 'n/a', 'n/w', 'hol', 'holiday', 'off', '-']:
                    summary["empty_cells_skipped"] += 1
                    continue

                date_header = df.columns[col_idx]
                parsed_date = parse_date_header(date_header)
                if not parsed_date:
                    continue

                country = detect_country_enhanced(text)
                if country == "UK":
                    summary["uk_jobs_skipped"] += 1
                    continue

                travel_day = text.lower().startswith(("tr", "tr/"))

                trip_records.append({
                    "employee": employee_name,
                    "date": parsed_date,
                    "country": country,
                    "travel_day": travel_day,
                    "text": text,
                    "row": row_idx + header_row + 1,
                    "col": col_idx + 1
                })

        aggregated_trips = aggregate_trips_enhanced(trip_records)

        for trip in aggregated_trips:
            try:
                emp_id = find_or_create_employee(trip["employee"], db_path=db_path)
                trip_id = save_trip(
                    emp_id,
                    trip["country"],
                    trip["entry_date"],
                    trip["exit_date"],
                    trip.get("travel_days", 0),
                    db_path=db_path
                )
                if trip_id:
                    summary["trips_added"] += 1
                    summary["trips"].append({
                        "id": trip_id,
                        "employee": trip["employee"],
                        "country": trip["country"],
                        "entry_date": trip["entry_date"],
                        "exit_date": trip["exit_date"],
                        "travel_days": trip.get("travel_days", 0),
                        "total_days": (trip["exit_date"] - trip["entry_date"]).days + 1
                    })
                else:
                    summary["duplicates_skipped"] += 1
            except Exception as e:
                summary["errors"].append(str(e))

        return summary

    except Exception as e:
        summary["errors"].append(str(e))
        return summary
