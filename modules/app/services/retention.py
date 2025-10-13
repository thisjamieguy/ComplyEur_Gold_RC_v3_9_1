import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List


def calculate_retention_cutoff(retention_months: int) -> str:
    """Calculate the cutoff date for retention policy.
    Returns YYYY-MM-DD string."""
    cutoff_date = datetime.now().date() - timedelta(days=retention_months * 30)
    return cutoff_date.strftime('%Y-%m-%d')


def get_expired_trips(db_path: str, retention_months: int) -> List[Dict]:
    """Get list of trips that are past the retention period."""
    cutoff_date = calculate_retention_cutoff(retention_months)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT trips.id, trips.employee_id, employees.name, 
               trips.country, trips.entry_date, trips.exit_date
        FROM trips
        JOIN employees ON trips.employee_id = employees.id
        WHERE trips.exit_date < ?
        ORDER BY trips.exit_date ASC
    ''', (cutoff_date,))
    
    trips = [dict(row) for row in c.fetchall()]
    conn.close()
    return trips


def purge_expired_trips(db_path: str, retention_months: int) -> Dict[str, int]:
    """Delete trips that are past the retention period.
    Returns dict with count of deleted trips and affected employees."""
    cutoff_date = calculate_retention_cutoff(retention_months)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get count before deletion
    c.execute('SELECT COUNT(*) FROM trips WHERE exit_date < ?', (cutoff_date,))
    trips_count = c.fetchone()[0]
    
    # Get affected employee IDs
    c.execute('SELECT DISTINCT employee_id FROM trips WHERE exit_date < ?', (cutoff_date,))
    affected_employees = [row[0] for row in c.fetchall()]
    
    # Delete expired trips
    c.execute('DELETE FROM trips WHERE exit_date < ?', (cutoff_date,))
    
    # Delete employees with no remaining trips
    c.execute('''
        DELETE FROM employees 
        WHERE id NOT IN (SELECT DISTINCT employee_id FROM trips)
    ''')
    employees_deleted = c.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        'trips_deleted': trips_count,
        'employees_affected': len(affected_employees),
        'employees_deleted': employees_deleted,
        'cutoff_date': cutoff_date
    }


def anonymize_employee(db_path: str, employee_id: int) -> Dict:
    """Replace employee name with anonymous identifier while keeping trip data."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get current name
    c.execute('SELECT name FROM employees WHERE id = ?', (employee_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return {'success': False, 'error': 'Employee not found'}
    
    old_name = result[0]
    anonymous_name = f"Employee #{employee_id:04d}"
    
    # Update name
    c.execute('UPDATE employees SET name = ? WHERE id = ?', (anonymous_name, employee_id))
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'employee_id': employee_id,
        'old_name': old_name,
        'new_name': anonymous_name
    }

