"""
TEST OVERVIEW PAGE - TEMPORARY TESTING ROUTE
This file can be safely deleted when testing is complete.
To remove: Delete this file and remove the import/registration in app.py
"""

from flask import render_template, Blueprint, jsonify
from datetime import datetime
import sqlite3
import os
from app.services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining

# Create blueprint for test overview
test_bp = Blueprint('test_overview', __name__)

def get_db_path():
    """Get the database path"""
    return os.path.join(os.path.dirname(__file__), 'eu_tracker.db')

def get_latest_excel_file():
    """Find the most recent Excel file in uploads folder"""
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(upload_folder):
        return None
    
    excel_files = [f for f in os.listdir(upload_folder) if f.endswith(('.xlsx', '.xls'))]
    if not excel_files:
        return None
    
    # Get the most recently modified file
    latest_file = max(excel_files, key=lambda f: os.path.getmtime(os.path.join(upload_folder, f)))
    return os.path.join(upload_folder, latest_file)

def calculate_employee_summary():
    """
    Calculate summary data for all employees
    Returns list of dicts with employee travel data
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all employees
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()
    
    summary_data = []
    today = datetime.now().date()
    
    for emp in employees:
        emp_id = emp['id']
        emp_name = emp['name']
        
        # Get all trips for this employee
        c.execute('''
            SELECT entry_date, exit_date, country 
            FROM trips 
            WHERE employee_id = ? 
            ORDER BY entry_date DESC
        ''', (emp_id,))
        trips = c.fetchall()
        
        # Get total trip count
        trip_count = len(trips)
        
        # Calculate 90/180 day stats using rolling90 module
        trips_list = [
            {
                'entry_date': t['entry_date'],
                'exit_date': t['exit_date'],
                'country': t['country']
            } 
            for t in trips
        ]
        
        presence = presence_days(trips_list)
        days_used = days_used_in_window(presence, today)
        days_remaining = calculate_days_remaining(presence, today)
        
        # Determine status
        if days_used >= 90:
            status = 'danger'  # Exceeded
            status_emoji = '🔴'
        elif days_used >= 85:
            status = 'warning'  # Warning zone
            status_emoji = '🟠'
        else:
            status = 'safe'  # Safe
            status_emoji = '🟢'
        
        # Get most recent country
        recent_country = None
        last_exit_date = None
        if trips:
            most_recent_trip = trips[0]  # Already ordered by entry_date DESC
            recent_country = most_recent_trip['country']
            last_exit_date = most_recent_trip['exit_date']
        
        # Calculate next eligible entry date (if over 90 days)
        next_eligible = None
        if days_used >= 90:
            # Find when they can re-enter (simplified calculation)
            # This would need the full earliest_safe_entry logic for accuracy
            from app.services.rolling90 import earliest_safe_entry
            safe_date = earliest_safe_entry(presence, today)
            if safe_date:
                next_eligible = safe_date.strftime('%d-%m-%Y')
        
        summary_data.append({
            'name': emp_name,
            'current_country': recent_country or 'N/A',
            'total_trips': trip_count,
            'days_used': days_used,
            'days_remaining': days_remaining,
            'status': status,
            'status_emoji': status_emoji,
            'next_eligible': next_eligible or 'N/A',
            'last_exit': last_exit_date or 'N/A'
        })
    
    conn.close()
    return summary_data

@test_bp.route('/test-overview')
def test_overview():
    """
    TEST OVERVIEW PAGE - Display employee travel summary
    Shows current data from database with calculated 90/180 day stats
    """
    try:
        # Get summary data
        employee_data = calculate_employee_summary()
        
        # Get import metadata
        latest_excel = get_latest_excel_file()
        last_import_time = None
        excel_filename = None
        
        if latest_excel:
            excel_filename = os.path.basename(latest_excel)
            last_import_time = datetime.fromtimestamp(os.path.getmtime(latest_excel))
        
        # Calculate totals
        total_employees = len(employee_data)
        total_trips = sum(emp['total_trips'] for emp in employee_data)
        
        return render_template(
            'test_overview.html',
            employees=employee_data,
            total_employees=total_employees,
            total_trips=total_trips,
            last_import=last_import_time,
            excel_file=excel_filename,
            load_time=datetime.now()
        )
    
    except Exception as e:
        error_message = f"Error loading data: {str(e)}"
        return render_template(
            'test_overview.html',
            employees=[],
            total_employees=0,
            total_trips=0,
            error=error_message,
            load_time=datetime.now()
        )

@test_bp.route('/test-overview/reload')
def test_overview_reload():
    """
    RELOAD ENDPOINT - Reimport Excel data
    This triggers a fresh import from the latest Excel file
    """
    try:
        from importer import process_excel
        
        latest_excel = get_latest_excel_file()
        if not latest_excel:
            return jsonify({
                'success': False,
                'error': 'No Excel file found in uploads folder'
            })
        
        # Process the Excel file
        summary = process_excel(latest_excel, db_path=get_db_path())
        
        return jsonify({
            'success': True,
            'trips_added': summary.get('trips_added', 0),
            'duplicates_skipped': summary.get('duplicates_skipped', 0),
            'uk_jobs_skipped': summary.get('uk_jobs_skipped', 0),
            'errors': summary.get('errors', [])
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


