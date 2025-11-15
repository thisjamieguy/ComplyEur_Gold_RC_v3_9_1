"""Employee management routes."""

from __future__ import annotations

from flask import flash, jsonify, redirect, request, url_for

from app.middleware.auth import login_required
from .base import main_bp, get_db, write_audit, current_actor, logger


@main_bp.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'})
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO employees (name) VALUES (?)', (name,))
        employee_id = c.lastrowid
        conn.commit()
        
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'employee_added', 'admin', {
            'employee_id': employee_id,
            'employee_name': name
        })
        
        return jsonify({'success': True, 'employee_id': employee_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


@main_bp.route('/delete_employee/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    """Delete an employee and all their trips"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('DELETE FROM trips WHERE employee_id = ?', (employee_id,))
        trips_deleted = c.rowcount
        
        c.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
        employee_deleted = c.rowcount
        
        conn.commit()
        
        if employee_deleted > 0:
            flash(f'Employee and {trips_deleted} associated trip(s) deleted successfully.', 'success')
            try:
                from flask import current_app
                CONFIG = current_app.config.get('CONFIG', {})
                audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
                write_audit(audit_log_path, 'employee_delete', current_actor(), {
                    'employee_id': employee_id,
                    'trips_deleted': trips_deleted
                })
            except Exception:
                pass
        else:
            flash('Employee not found.', 'error')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        flash(f'Error deleting employee: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))
    finally:
        if 'conn' in locals():
            conn.close()


@main_bp.route('/api/employees/search')
@login_required
def api_employees_search():
    """Search employees by name for autocomplete fields."""
    q = request.args.get('q', '').strip().lower()
    conn = get_db()
    c = conn.cursor()
    try:
        if q:
            c.execute('SELECT id, name FROM employees WHERE LOWER(name) LIKE ?', (f'%{q}%',))
        else:
            c.execute('SELECT id, name FROM employees ORDER BY name LIMIT 20')
        rows = [{'id': r['id'], 'name': r['name']} for r in c.fetchall()]
    finally:
        conn.close()
    # Provide both 'employees' and 'results' for compatibility with existing JS
    return jsonify({'employees': rows, 'results': rows})
