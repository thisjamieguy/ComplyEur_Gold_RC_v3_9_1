from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_file
import hashlib
import sqlite3
import logging
import traceback
from datetime import datetime, timedelta
from functools import wraps
import os
import re
import openpyxl
from werkzeug.utils import secure_filename
from config import load_config, get_session_lifetime, save_config

# Import service modules with error handling
logger = logging.getLogger(__name__)

try:
    from .services.hashing import Hasher
    logger.info("Successfully imported hashing service")
except Exception as e:
    logger.error(f"Failed to import hashing service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.audit import write_audit
    logger.info("Successfully imported audit service")
except Exception as e:
    logger.error(f"Failed to import audit service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.retention import purge_expired_trips, get_expired_trips, anonymize_employee
    logger.info("Successfully imported retention service")
except Exception as e:
    logger.error(f"Failed to import retention service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.dsar import create_dsar_export, delete_employee_data, rectify_employee_name, get_employee_data
    logger.info("Successfully imported dsar service")
except Exception as e:
    logger.error(f"Failed to import dsar service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.exports import export_trips_csv, export_employee_report_pdf, export_all_employees_report_pdf
    logger.info("Successfully imported exports service")
except Exception as e:
    logger.error(f"Failed to import exports service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.rolling90 import presence_days, days_used_in_window, earliest_safe_entry, calculate_days_remaining, get_risk_level, days_until_compliant
    logger.info("Successfully imported rolling90 service")
except Exception as e:
    logger.error(f"Failed to import rolling90 service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.trip_validator import validate_trip, validate_date_range
    logger.info("Successfully imported trip_validator service")
except Exception as e:
    logger.error(f"Failed to import trip_validator service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.compliance_forecast import (
        calculate_future_job_compliance, 
        get_all_future_jobs_for_employee,
        calculate_what_if_scenario,
        get_risk_level_for_forecast
    )
    logger.info("Successfully imported compliance_forecast service")
except Exception as e:
    logger.error(f"Failed to import compliance_forecast service: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from .services.backup import create_backup, auto_backup_if_needed, list_backups
    logger.info("Successfully imported backup service")
except Exception as e:
    logger.error(f"Failed to import backup service: {e}")
    logger.error(traceback.format_exc())
    raise

import io
import csv
import zipfile
import secrets
import json
import atexit
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create blueprint
main_bp = Blueprint('main', __name__)

# Rate limiting for login attempts
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5 minutes

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('main.login'))
        
        # Check session timeout
        if 'last_activity' in session:
            try:
                last_activity_str = session['last_activity']
                # Handle different datetime formats safely
                if isinstance(last_activity_str, str):
                    if 'Z' in last_activity_str:
                        last_activity_str = last_activity_str.replace('Z', '+00:00')
                    last_activity = datetime.fromisoformat(last_activity_str)
                    # Convert to naive datetime for comparison
                    if last_activity.tzinfo:
                        last_activity = last_activity.replace(tzinfo=None)
                else:
                    last_activity = datetime.now()

                if datetime.now() - last_activity > timedelta(minutes=30):
                    session.clear()  # Clear entire session
                    return redirect(url_for('main.login'))
            except (ValueError, TypeError, AttributeError):
                # If datetime parsing fails, clear session
                session.clear()
                return redirect(url_for('main.login'))
        
        # Update last activity
        from datetime import timezone
        session['last_activity'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Get database connection"""
    from flask import current_app
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def verify_and_upgrade_password(stored_hash, password):
    """Verify password and upgrade hash if needed"""
    try:
        hasher = Hasher()
        # Try to verify with stored hash
        if hasher.verify(stored_hash, password):
            # Check if we need to upgrade the hash
            if not stored_hash.startswith('$argon2'):
                # Upgrade to argon2
                new_hash = hasher.hash(password)
                return True, new_hash
            return True, None
    except Exception:
        pass
    return False, None

def allowed_file(filename):
    """Check if file extension is allowed"""
    from flask import current_app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/privacy')
def privacy():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    return render_template('privacy.html',
                         current_date=datetime.now().strftime('%Y-%m-%d'),
                         retention_months=CONFIG.get('RETENTION_MONTHS', 36),
                         session_timeout_minutes=CONFIG.get('SESSION_IDLE_TIMEOUT_MINUTES', 30),
                         max_login_attempts=MAX_ATTEMPTS,
                         rate_limit_window=ATTEMPT_WINDOW_SECONDS // 60)

@main_bp.route('/help')
@login_required
def help_page():
    """Display help and tutorial page."""
    import json
    help_file = os.path.join(os.path.dirname(__file__), '..', 'help_content.json')
    
    try:
        with open(help_file, 'r') as f:
            help_content = json.load(f)
    except Exception as e:
        # Fallback if help file doesn't exist
        help_content = {
            'page_title': 'Help & User Guide',
            'page_subtitle': 'Learn how to use the EU Trip Tracker',
            'sections': [],
            'tutorial_steps': [],
            'quick_tips': []
        }
    
    return render_template('help.html', help_content=help_content)

@main_bp.route('/entry-requirements')
@login_required
def entry_requirements():
    """Display EU entry requirements for UK citizens."""
    from flask import current_app
    return render_template('entry_requirements.html', countries=current_app.config['EU_ENTRY_DATA'])

@main_bp.route('/api/entry-requirements')
@login_required
def entry_requirements_api():
    """API endpoint returning EU entry requirements as JSON."""
    from flask import current_app
    return jsonify(current_app.config['EU_ENTRY_DATA'])

@main_bp.route('/api/entry-requirements/reload', methods=['POST'])
@login_required
def reload_entry_requirements():
    """Reload EU entry requirements data from JSON file."""
    from flask import current_app
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_entry_requirements.json')
        with open(data_file_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        current_app.config['EU_ENTRY_DATA'] = new_data
        return jsonify({
            'success': True, 
            'message': f'Successfully reloaded {len(new_data)} countries',
            'count': len(new_data)
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error reloading data: {str(e)}'
        }), 500

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from flask import current_app
        CONFIG = current_app.config['CONFIG']
        ip = request.remote_addr or 'local'
        from datetime import timezone
        now = datetime.now(timezone.utc)
        attempts = LOGIN_ATTEMPTS.get(ip)
        if attempts:
            count, first_ts = attempts
            if (now - first_ts).total_seconds() <= ATTEMPT_WINDOW_SECONDS and count >= MAX_ATTEMPTS:
                write_audit(CONFIG['AUDIT_LOG_PATH'], 'login_rate_limited', 'admin', {'ip': ip})
                return render_template('login.html', error='Too many attempts. Try again later.')
            if (now - first_ts).total_seconds() > ATTEMPT_WINDOW_SECONDS:
                LOGIN_ATTEMPTS[ip] = (0, now)
        else:
            LOGIN_ATTEMPTS[ip] = (0, now)

        password = request.form.get('password', '')
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT password_hash FROM admin WHERE id = 1')
        admin = c.fetchone()
        if not admin:
            conn.close()
            return redirect(url_for('main.setup'))
        ok, new_hash = verify_and_upgrade_password(admin['password_hash'], password)
        if ok:
            if new_hash:
                c.execute('UPDATE admin SET password_hash = ? WHERE id = 1', (new_hash,))
                conn.commit()
            conn.close()
            session['logged_in'] = True
            from datetime import timezone
            session['last_activity'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'login_success', 'admin', {'ip': ip})
            return redirect(url_for('main.dashboard'))
        # failed
        conn.close()
        count, first_ts = LOGIN_ATTEMPTS.get(ip, (0, now))
        LOGIN_ATTEMPTS[ip] = (count + 1, first_ts)
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'login_failure', 'admin', {'ip': ip})
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@main_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """First-time setup to create admin account"""
    from .models import Admin
    
    # Check if admin already exists
    if Admin.exists():
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password:
            # Create admin account with provided password
            hasher = Hasher()
            password_hash = hasher.hash(password)
            Admin.set_password_hash(password_hash)
            return render_template('login.html', success='Admin account created successfully. Please log in.')
        else:
            return render_template('setup.html', error='Password is required')
    
    return render_template('setup.html')

@main_bp.route('/logout')
def logout():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    session.pop('logged_in', None)
    write_audit(CONFIG['AUDIT_LOG_PATH'], 'logout', 'admin', {})
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    # Get sort parameter from query string
    sort_by = request.args.get('sort', 'first_name')
    
    conn = get_db()
    c = conn.cursor()
    
    # Determine sort order based on parameter
    if sort_by == 'last_name':
        # Sort by last name (everything after the first space)
        c.execute('SELECT id, name FROM employees ORDER BY SUBSTR(name, INSTR(name, " ") + 1), name')
    else:
        # Default: sort by first name (full name)
        c.execute('SELECT id, name FROM employees ORDER BY name')
    
    employees = c.fetchall()
    employee_data = []
    at_risk_employees = []
    today = datetime.now().date()
    
    # Get risk thresholds from config
    risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {'green': 30, 'amber': 10})
    warning_threshold = CONFIG.get('FUTURE_JOB_WARNING_THRESHOLD', 80)
    
    # Track future compliance alerts summary
    future_alerts_red = 0
    future_alerts_yellow = 0
    future_alerts_green = 0

    for emp in employees:
        # Get all trips for this employee
        c.execute('SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?', (emp['id'],))
        trips = [{'entry_date': t['entry_date'], 'exit_date': t['exit_date'], 'country': t['country']} for t in c.fetchall()]
        
        # Calculate presence days and usage using new rolling90 module
        presence = presence_days(trips)
        days_used = days_used_in_window(presence, today)
        days_remaining = calculate_days_remaining(presence, today)
        risk_level = get_risk_level(days_remaining, risk_thresholds)
        
        # Calculate earliest safe entry date
        safe_entry = earliest_safe_entry(presence, today)
        
        # Calculate days until compliant for at-risk employees (days_remaining < 0)
        days_until_compliant_val = None
        compliance_date = None
        if days_remaining < 0:
            days_until_compliant_val, compliance_date = days_until_compliant(presence, today)

        # Get total trip count
        c.execute('SELECT COUNT(*) FROM trips WHERE employee_id = ?', (emp['id'],))
        trip_count = c.fetchone()[0]

        # Get next upcoming trip
        c.execute('SELECT country, entry_date FROM trips WHERE employee_id = ? AND entry_date > ? ORDER BY entry_date ASC LIMIT 1',
                 (emp['id'], today.strftime('%Y-%m-%d')))
        next_trip = c.fetchone()

        # Get recent trips for the card view
        c.execute('SELECT country, entry_date, exit_date FROM trips WHERE employee_id = ? ORDER BY exit_date DESC LIMIT 5', (emp['id'],))
        recent_trips = c.fetchall()
        
        # Calculate future job forecasts for this employee
        forecasts = get_all_future_jobs_for_employee(emp['id'], trips, warning_threshold)
        for forecast in forecasts:
            if forecast['risk_level'] == 'red':
                future_alerts_red += 1
            elif forecast['risk_level'] == 'yellow':
                future_alerts_yellow += 1
            else:
                future_alerts_green += 1
        
        # Create employee data object
        emp_data = {
            'id': emp['id'],
            'name': emp['name'],
            'days_used': days_used,
            'days_remaining': days_remaining,
            'risk_level': risk_level,
            'safe_entry_date': safe_entry,
            'trip_count': trip_count,
            'next_trip': next_trip,
            'recent_trips': recent_trips,
            'days_until_compliant': days_until_compliant_val,
            'compliance_date': compliance_date,
            'forecasts': forecasts
        }
        
        employee_data.append(emp_data)
        
        # Track at-risk employees (days_remaining < 0 or days_remaining < 10)
        if days_remaining < 10:
            at_risk_employees.append(emp_data)
    
    conn.close()
    
    # Get future job alerts summary
    future_alerts_summary = {
        'red': future_alerts_red,
        'yellow': future_alerts_yellow,
        'green': future_alerts_green
    }
    
    return render_template('dashboard.html', 
                         employees=employee_data, 
                         at_risk_employees=at_risk_employees,
                         future_alerts_summary=future_alerts_summary,
                         sort_by=sort_by,
                         risk_thresholds=risk_thresholds)

@main_bp.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get employee details
    c.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
    employee = c.fetchone()
    if not employee:
        conn.close()
        return "Employee not found", 404
    
    # Get all trips for this employee
    c.execute('SELECT * FROM trips WHERE employee_id = ? ORDER BY entry_date DESC', (employee_id,))
    trips = c.fetchall()
    
    # Convert trips to list of dicts
    trips_list = []
    for trip in trips:
        trips_list.append({
            'id': trip['id'],
            'country': trip['country'],
            'entry_date': trip['entry_date'],
            'exit_date': trip['exit_date'],
            'purpose': trip.get('purpose', '')
        })
    
    conn.close()
    
    return render_template('employee_detail.html', employee=employee, trips=trips_list)

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

@main_bp.route('/add_trip', methods=['POST'])
@login_required
def add_trip():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    employee_id = request.form.get('employee_id')
    country = request.form.get('country', '').strip()
    entry_date = request.form.get('entry_date')
    exit_date = request.form.get('exit_date')
    purpose = request.form.get('purpose', '').strip()
    
    if not all([employee_id, country, entry_date, exit_date]):
        return jsonify({'success': False, 'error': 'All fields are required'})
    
    # Validate dates
    try:
        entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
        exit_dt = datetime.strptime(exit_date, '%Y-%m-%d')
        if exit_dt <= entry_dt:
            return jsonify({'success': False, 'error': 'Exit date must be after entry date'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'})
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, purpose)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, country, entry_date, exit_date, purpose))
        trip_id = c.lastrowid
        conn.commit()
        
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'trip_added', 'admin', {
            'trip_id': trip_id,
            'employee_id': employee_id,
            'country': country,
            'entry_date': entry_date,
            'exit_date': exit_date
        })
        
        return jsonify({'success': True, 'trip_id': trip_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@main_bp.route('/bulk_add_trip')
@login_required
def bulk_add_trip():
    """Display bulk add trip form"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()
    conn.close()
    
    return render_template('bulk_add_trip.html', employees=employees)

@main_bp.route('/delete_trip/<int:trip_id>', methods=['POST'])
@login_required
def delete_trip(trip_id):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get trip details before deletion for audit
        c.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
        trip = c.fetchone()
        
        if not trip:
            return jsonify({'success': False, 'error': 'Trip not found'})
        
        c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        conn.commit()
        
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'trip_deleted', 'admin', {
            'trip_id': trip_id,
            'employee_id': trip['employee_id'],
            'country': trip['country'],
            'entry_date': trip['entry_date'],
            'exit_date': trip['exit_date']
        })
        
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# Additional missing routes
@main_bp.route('/import_excel')
@login_required
def import_excel():
    """Display import Excel form"""
    return render_template('import_excel.html')

@main_bp.route('/calendar/<int:employee_id>')
@login_required
def calendar(employee_id):
    """Display employee calendar"""
    from .models import Employee
    employee = Employee.get_by_id(employee_id)
    if not employee:
        return "Employee not found", 404
    return render_template('calendar.html', employee=employee)

@main_bp.route('/future_job_alerts')
@login_required
def future_job_alerts():
    """Display future job alerts"""
    return render_template('future_job_alerts.html')

@main_bp.route('/what_if_scenario')
@login_required
def what_if_scenario():
    """Display what-if scenario page"""
    return render_template('what_if_scenario.html')

@main_bp.route('/admin_privacy_tools')
@login_required
def admin_privacy_tools():
    """Display admin privacy tools"""
    return render_template('admin_privacy_tools.html')

@main_bp.route('/admin_settings')
@login_required
def admin_settings():
    """Display admin settings"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    return render_template('admin_settings.html', config=CONFIG)

@main_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change admin password"""
    return redirect(url_for('main.admin_settings'))

@main_bp.route('/delete_all_data', methods=['POST'])
@login_required
def delete_all_data():
    """Delete all data"""
    return redirect(url_for('main.admin_settings'))

@main_bp.route('/reset_admin_password', methods=['GET', 'POST'])
def reset_admin_password():
    """Emergency admin password reset - remove this route after use"""
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        if new_password and len(new_password) >= 6:
            from .models import Admin
            hasher = Hasher()
            password_hash = hasher.hash(new_password)
            Admin.set_password_hash(password_hash)
            return render_template('login.html', success='Admin password reset successfully. Please log in with your new password.')
        else:
            return render_template('reset_password.html', error='Password must be at least 6 characters')
    
    return render_template('reset_password.html')

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {error}")
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error: {error}")
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500

@main_bp.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500
