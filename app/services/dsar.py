import json
import csv
import zipfile
import io
import os
from datetime import datetime
from typing import Dict, Optional

from app.repositories import dsar_repository


def get_employee_data(db_path: str, employee_id: int) -> Optional[Dict]:
    """Retrieve all data for an employee."""
    employee = dsar_repository.fetch_employee(db_path, employee_id)
    if not employee:
        return None
    trips = dsar_repository.fetch_employee_trips(db_path, employee_id)
    return {'employee': employee, 'trips': trips}


def create_dsar_export(db_path: str, employee_id: int, export_dir: str, 
                       retention_months: int) -> Dict:
    """Create a DSAR ZIP export for an employee.
    Returns dict with file_path and summary."""
    
    data = get_employee_data(db_path, employee_id)
    if not data:
        return {'success': False, 'error': 'Employee not found'}
    
    employee = data['employee']
    trips = data['trips']
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Create export directory if needed
    os.makedirs(export_dir, exist_ok=True)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Employee JSON
        employee_json = {
            'employee_id': employee['id'],
            'name': employee['name'],
            'export_timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        zipf.writestr('employee.json', json.dumps(employee_json, indent=2))
        
        # 2. Trips CSV
        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(csv_buffer, 
                                     fieldnames=['country', 'entry_date', 'exit_date', 
                                                'travel_days', 'created_at'])
        csv_writer.writeheader()
        for trip in trips:
            csv_writer.writerow({
                'country': trip['country'],
                'entry_date': trip['entry_date'],
                'exit_date': trip['exit_date'],
                'travel_days': trip.get('travel_days', 0) or 0,
                'created_at': trip.get('created_at', '')
            })
        zipf.writestr('trips.csv', csv_buffer.getvalue())
        
        # 3. Processing notes
        processing_notes = f"""EU TRIP TRACKER - DATA SUBJECT ACCESS REQUEST EXPORT

Employee: {employee['name']} (ID: {employee['id']})
Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

PURPOSE OF PROCESSING:
This system processes minimal personal data to track compliance with the Schengen 90/180-day rule
for business travel. The data is used for:
- Monitoring employee EU travel days
- Preventing compliance violations
- Generating travel reports for management

LAWFUL BASIS:
- Employee data: Legitimate Interests (compliance tracking)
- Trip data: Legal Obligation (Schengen regulation compliance)

DATA STORED:
- Employee name (for identification)
- Trip records: country code, entry date, exit date, travel days, creation timestamp
- Private trips: stored with dates only, country redacted as "XX", purpose as "PRIVATE_REDACTED"
- No special category data
- No profiling or automated decision-making

RETENTION POLICY:
- Trips are retained for {retention_months} months after exit_date
- Employee records deleted when no trips remain
- Current retention cutoff: {(datetime.now().date()).strftime('%Y-%m-%d')} minus {retention_months} months

STORAGE LOCATION:
- Local SQLite database (eu_tracker.db)
- No cloud storage
- No third-party sharing
- No cross-border transfers

ACCESS CONTROL:
- Admin-only access via password-protected login
- Session cookies with HttpOnly and SameSite=Strict
- Audit logging for all admin actions

YOUR RIGHTS:
- Right to access: This export
- Right to rectification: Contact admin to update name
- Right to erasure: Contact admin to delete all your data
- Right to restrict processing: Contact admin
- Right to data portability: This export (JSON + CSV format)
- Right to object: Contact admin

HOW TO EXERCISE YOUR RIGHTS:
Contact the system administrator to request changes, deletions, or further information.

FILES IN THIS EXPORT:
- employee.json: Your employee record
- trips.csv: All your trip records in CSV format
- processing-notes.txt: This file

Total trips exported: {len(trips)}
"""
        zipf.writestr('processing-notes.txt', processing_notes)
    
    # Save ZIP to disk
    safe_name = employee['name'].replace(' ', '_').replace('/', '_')
    zip_filename = f"dsar_export_{safe_name}_{timestamp}.zip"
    zip_path = os.path.join(export_dir, zip_filename)
    
    with open(zip_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    
    return {
        'success': True,
        'file_path': zip_path,
        'filename': zip_filename,
        'employee_id': employee['id'],
        'employee_name': employee['name'],
        'trips_count': len(trips),
        'timestamp': timestamp
    }


def delete_employee_data(db_path: str, employee_id: int) -> Dict:
    """Hard delete employee and all associated trips.
    Returns summary of deletion."""
    result = dsar_repository.delete_employee_and_trips(db_path, employee_id)
    if not result:
        return {'success': False, 'error': 'Employee not found'}
    return {
        'success': True,
        'employee_id': employee_id,
        'employee_name': result['name'],
        'trips_deleted': result['trips_deleted']
    }


def rectify_employee_name(db_path: str, employee_id: int, new_name: str) -> Dict:
    """Update employee name."""
    if not new_name or not new_name.strip():
        return {'success': False, 'error': 'Name cannot be empty'}
    
    old_name = dsar_repository.fetch_employee_name(db_path, employee_id)
    if not old_name:
        return {'success': False, 'error': 'Employee not found'}
    
    dsar_repository.update_employee_name(db_path, employee_id, new_name.strip())
    return {
        'success': True,
        'employee_id': employee_id,
        'old_name': old_name,
        'new_name': new_name.strip()
    }

