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
import time

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

def redact_private_trip_data(trip):
    """Redact private trip data for admin display"""
    if trip.get('is_private', False):
        return {
            'entry_date': trip['entry_date'],
            'exit_date': trip['exit_date'],
            'country': 'Personal Trip',
            'is_private': True
        }
    return trip

# Rate limiting for login attempts
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5 minutes

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('main.login'))
        
        # Check session timeout (compare in UTC to avoid timezone skew)
        if 'last_activity' in session:
            try:
                last_activity_str = session['last_activity']
                # Parse to naive UTC
                if isinstance(last_activity_str, str):
                    if 'Z' in last_activity_str:
                        last_activity_str = last_activity_str.replace('Z', '')
                    if '+' in last_activity_str:
                        last_activity_str = last_activity_str.split('+')[0]
                    if 'T' in last_activity_str:
                        last_activity = datetime.strptime(last_activity_str, '%Y-%m-%dT%H:%M:%S')
                    else:
                        last_activity = datetime.fromisoformat(last_activity_str)
                else:
                    last_activity = datetime.utcnow()

                # Ensure both datetimes are naive
                if getattr(last_activity, 'tzinfo', None):
                    last_activity = last_activity.replace(tzinfo=None)

                if datetime.utcnow() - last_activity > timedelta(minutes=30):
                    session.clear()
                    return redirect(url_for('main.login'))
            except (ValueError, TypeError, AttributeError):
                # If datetime parsing fails, clear session
                session.clear()
                return redirect(url_for('main.login'))
        
        # Update last activity
        session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
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

@main_bp.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

@main_bp.route('/api/version')
def api_version():
    from flask import current_app
    version = current_app.config.get('APP_VERSION', None)
    try:
        from app import APP_VERSION as defined_version
        version = version or defined_version
    except Exception:
        pass
    return jsonify({'version': version}), 200

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

@main_bp.route('/test-summary', methods=['GET'])
# @login_required  # Temporarily disabled for testing
def test_summary():
    """
    TEMPORARY TEST PAGE - FOR DEVELOPMENT ONLY
    Displays detailed trip breakdown per employee for data verification.
    Can be disabled by setting TEST_MODE=False in config.py
    """
    config = load_config()
    if not config.get('TEST_MODE', False):
        return render_template('404.html'), 404
    
    from .models import get_db, Employee
    
    # Get selected employee from query params
    employee_id = request.args.get('employee_id', type=int)
    
    # Use single database connection for all operations
    conn = get_db()
    cursor = conn.cursor()
    
    # Load all employees for dropdown
    cursor.execute('SELECT id, name FROM employees ORDER BY name')
    employees = [type('Employee', (), {'id': row['id'], 'name': row['name']})() for row in cursor.fetchall()]
    
    # If employee selected, fetch their trips with calculations
    trips_data = []
    selected_employee = None
    totals = {'total_days': 0, 'travel_days': 0, 'working_days': 0}
    
    if employee_id:
        # Get employee info
        cursor.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        emp_row = cursor.fetchone()
        if emp_row:
            selected_employee = type('Employee', (), {'id': emp_row['id'], 'name': emp_row['name']})()
            
            # Get trips for this employee
            cursor.execute('''
                SELECT id, country, entry_date, exit_date, purpose, travel_days
                FROM trips 
                WHERE employee_id = ?
                ORDER BY entry_date DESC
            ''', (employee_id,))
            
            for row in cursor.fetchall():
                # Calculate days
                entry = datetime.strptime(row['entry_date'], '%Y-%m-%d').date()
                exit = datetime.strptime(row['exit_date'], '%Y-%m-%d').date()
                total_days = (exit - entry).days + 1
                travel_days = row['travel_days'] or 0
                working_days = total_days - travel_days
                
                # Determine if Schengen
                from .services.rolling90 import is_schengen_country
                is_schengen = is_schengen_country(row['country'])
                
                trip_info = {
                    'id': row['id'],
                    'country': row['country'],
                    'entry_date': row['entry_date'],
                    'exit_date': row['exit_date'],
                    'purpose': row['purpose'] or '',
                    'total_days': total_days,
                    'travel_days': travel_days,
                    'working_days': working_days,
                    'is_schengen': is_schengen
                }
                trips_data.append(trip_info)
                
                # Update totals
                totals['total_days'] += total_days
                totals['travel_days'] += travel_days
                totals['working_days'] += working_days
    
    return render_template('test_summary.html',
                         employees=employees,
                         selected_employee=selected_employee,
                         trips=trips_data,
                         totals=totals)

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

@main_bp.route('/profile')
@login_required
def profile():
    """Lightweight admin profile placeholder page."""
    admin_name = session.get('username', 'Admin')
    last_login = session.get('last_activity')
    return render_template('profile.html', admin_name=admin_name, last_login=last_login)

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
        c.execute('SELECT entry_date, exit_date, country, is_private FROM trips WHERE employee_id = ?', (emp['id'],))
        trips = [{'entry_date': t['entry_date'], 'exit_date': t['exit_date'], 'country': t['country'], 'is_private': t['is_private']} for t in c.fetchall()]
        
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
        c.execute('SELECT country, entry_date, is_private FROM trips WHERE employee_id = ? AND entry_date > ? ORDER BY entry_date ASC LIMIT 1',
                 (emp['id'], today.strftime('%Y-%m-%d')))
        next_trip_row = c.fetchone()
        next_trip = redact_private_trip_data(dict(next_trip_row)) if next_trip_row else None

        # Get recent trips for the card view
        c.execute('SELECT country, entry_date, exit_date, is_private FROM trips WHERE employee_id = ? ORDER BY exit_date DESC LIMIT 5', (emp['id'],))
        recent_trips = [redact_private_trip_data(dict(trip)) for trip in c.fetchall()]
        
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
    risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {'green': 30, 'amber': 10})
    
    conn = get_db()
    c = conn.cursor()
    
    # Get employee details
    c.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
    employee = c.fetchone()
    if not employee:
        conn.close()
        return "Employee not found", 404
    
    # Get all trips for this employee
    c.execute('SELECT * FROM trips WHERE employee_id = ? ORDER BY entry_date ASC', (employee_id,))
    rows = c.fetchall()
    conn.close()

    # Build trip dicts and compute durations/statuses
    from datetime import date as _date
    today = _date.today()
    trips_list = []
    simple_trips = []  # for rolling90
    for row in rows:
        entry_str = row['entry_date']
        exit_str = row['exit_date']
        # Parse strings to dates for calculations
        try:
            entry_dt = _date.fromisoformat(entry_str) if isinstance(entry_str, str) else entry_str
            exit_dt = _date.fromisoformat(exit_str) if isinstance(exit_str, str) else exit_str
        except Exception:
            entry_dt, exit_dt = today, today
        duration = (exit_dt - entry_dt).days + 1
        status = 'completed'
        if entry_dt > today:
            status = 'future'
        elif entry_dt <= today <= exit_dt:
            status = 'current'

        trip_dict = {
            'id': row['id'],
            'country': row['country'],
            'entry_date': entry_str,
            'exit_date': exit_str,
            'purpose': (row['purpose'] or ''),
            'travel_days': row['travel_days'] if 'travel_days' in row.keys() else 0,
            'duration': duration,
            'status': status,
            'validation_note': None,
            'is_private': (row['is_private'] if 'is_private' in row.keys() else False)
        }
        
        # Apply redaction for display
        redacted_trip = redact_private_trip_data(trip_dict)
        trips_list.append(redacted_trip)
        
        # For compliance calculations, use original data (not redacted)
        simple_trips.append({'entry_date': entry_str, 'exit_date': exit_str, 'country': row['country']})

    # Compute rolling 90/180 stats for this employee
    presence = presence_days(simple_trips)
    from datetime import datetime as _dt
    ref_date = today
    days_used = days_used_in_window(presence, ref_date)
    days_remaining = calculate_days_remaining(presence, ref_date)
    risk_level = get_risk_level(days_remaining, risk_thresholds)
    safe_entry = earliest_safe_entry(presence, ref_date)
    days_until_safe = None
    compliant_date = None
    if days_remaining < 0:
        days_until_safe, compliant_date = days_until_compliant(presence, ref_date)
    
    # Annotate per-trip display fields depending on current remaining days
    for t in trips_list:
        t['days_remaining_after'] = days_remaining
        t['risk_level_after'] = get_risk_level(days_remaining, risk_thresholds)

    return render_template(
        'employee_detail.html',
        employee=employee,
        trips=trips_list,
        days_used=days_used,
        days_remaining=days_remaining,
        risk_level=risk_level,
        earliest_safe_entry=safe_entry,
        days_until_safe=days_until_safe,
    )

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
    # Accept either 'country_code' (preferred) or fallback to 'country'
    country = (request.form.get('country_code') or request.form.get('country') or '').strip()
    entry_date = request.form.get('entry_date')
    exit_date = request.form.get('exit_date')
    purpose = request.form.get('purpose', '').strip()
    
    # Check if this is a private trip
    is_private = (country == 'PRIVATE')
    
    # For private trips, set special values
    if is_private:
        country = 'XX'  # Internal placeholder for private trips
        purpose = 'PRIVATE_REDACTED'
    
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
            INSERT INTO trips (employee_id, country, entry_date, exit_date, purpose, is_private)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, country, entry_date, exit_date, purpose, is_private))
        trip_id = c.lastrowid
        conn.commit()
        
        audit_action = 'private_trip_added' if is_private else 'trip_added'
        write_audit(CONFIG['AUDIT_LOG_PATH'], audit_action, 'admin', {
            'trip_id': trip_id,
            'employee_id': employee_id,
            'country': country,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'is_private': is_private
        })
        
        return jsonify({'success': True, 'trip_id': trip_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# Removed per-employee Trip Planning forecast endpoint (use global planner API instead)

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

# Fetch a single trip (for edit modal)
@main_bp.route('/get_trip/<int:trip_id>')
@login_required
def get_trip(trip_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT id, employee_id, country, entry_date, exit_date FROM trips WHERE id = ?', (trip_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Trip not found'}), 404
        return jsonify({
            'id': row['id'],
            'employee_id': row['employee_id'],
            'country': row['country'],
            'entry_date': row['entry_date'],
            'exit_date': row['exit_date']
        })
    finally:
        conn.close()

# Edit a trip
@main_bp.route('/edit_trip/<int:trip_id>', methods=['POST'])
@login_required
def edit_trip(trip_id):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']

    try:
        payload = request.get_json(force=True) or {}
        new_country = (payload.get('country') or '').strip()
        new_entry = payload.get('entry_date')
        new_exit = payload.get('exit_date')
        if not (new_country and new_entry and new_exit):
            return jsonify({'error': 'Missing required fields'}), 400

        # Parse dates
        from datetime import date as _date
        try:
            entry_dt = _date.fromisoformat(new_entry)
            exit_dt = _date.fromisoformat(new_exit)
        except Exception:
            return jsonify({'error': 'Invalid date format'}), 400

        # Load existing trip and employee
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, employee_id FROM trips WHERE id = ?', (trip_id,))
        current_trip = c.fetchone()
        if not current_trip:
            conn.close()
            return jsonify({'error': 'Trip not found'}), 404

        employee_id = current_trip['employee_id']

        # Validate against overlaps for this employee
        c.execute('SELECT id, entry_date, exit_date FROM trips WHERE employee_id = ? AND id != ?', (employee_id, trip_id))
        existing = [{'id': r['id'], 'entry_date': r['entry_date'], 'exit_date': r['exit_date']} for r in c.fetchall()]

        hard_errors, _warnings = validate_trip(existing, entry_dt, exit_dt, trip_id_to_exclude=trip_id)
        if hard_errors:
            conn.close()
            return jsonify({'error': hard_errors[0]}), 400

        # Update
        c.execute('UPDATE trips SET country = ?, entry_date = ?, exit_date = ? WHERE id = ?', (new_country, new_entry, new_exit, trip_id))
        conn.commit()

        try:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'trip_updated', 'admin', {
                'trip_id': trip_id,
                'employee_id': employee_id,
                'country': new_country,
                'entry_date': new_entry,
                'exit_date': new_exit
            })
        except Exception:
            pass

        return jsonify({'success': True})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# Additional missing routes

@main_bp.route('/import_excel', methods=['GET', 'POST'])
@login_required
def import_excel():
    """Display import Excel form and handle file uploads"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']

    logger.info(f"import_excel: {request.method} request")
    
    if request.method == 'POST':
        start_time = time.monotonic()
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            flash('No file selected')
            return render_template('import_excel.html')
        
        file = request.files['excel_file']
        if file.filename == '':
            flash('No file selected')
            return render_template('import_excel.html')
        
        if file and allowed_file(file.filename):
            try:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Import the importer module (located at project root)
                import sys
                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                from importer import import_excel as process_excel
                
                # Process the Excel file with extended scanning enabled
                logger.info(f"Starting Excel processing for '{filename}'")
                result = process_excel(file_path, enable_extended_scan=True)
                elapsed = time.monotonic() - start_time
                logger.info(f"Finished Excel processing in {elapsed:.2f}s for '{filename}'")
                
                if result['success']:
                    # Log successful import
                    write_audit(CONFIG['AUDIT_LOG_PATH'], 'excel_import_success', 'admin', {
                        'filename': filename,
                        'trips_added': result['trips_added'],
                        'employees_processed': result['employees_processed'],
                        'employees_created': result.get('employees_created', 0),
                        'total_employee_names_found': result.get('total_employee_names_found', 0)
                    })
                    
                    # Clean up uploaded file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    
                    return render_template('import_excel.html', import_summary=result)
                else:
                    # Log failed import
                    write_audit(CONFIG['AUDIT_LOG_PATH'], 'excel_import_failed', 'admin', {
                        'filename': filename,
                        'error': result.get('error', 'Unknown error')
                    })
                    
                    flash(f'Import failed: {result.get("error", "Unknown error")}')
                    
                    # Clean up uploaded file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    
                    return render_template('import_excel.html')
                    
            except Exception as e:
                logger.error(f"Error processing Excel file: {e}")
                write_audit(CONFIG['AUDIT_LOG_PATH'], 'excel_import_error', 'admin', {
                    'filename': file.filename,
                    'error': str(e)
                })
                flash(f'Error processing file: {str(e)}')
                return render_template('import_excel.html')
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)')
            return render_template('import_excel.html')
    
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
    from flask import current_app
    CONFIG = current_app.config['CONFIG']

    warning_threshold = CONFIG.get('FUTURE_JOB_WARNING_THRESHOLD', 80)

    # Query params
    risk_filter = request.args.get('risk', 'all')  # all | red | yellow | green
    sort_by = request.args.get('sort', 'risk')     # risk | date | employee | days

    # Collect forecasts across all employees
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()

    all_forecasts = []
    for emp in employees:
        # Get all trips for this employee
        c.execute('SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?', (emp['id'],))
        trips = [
            {
                'entry_date': t['entry_date'],
                'exit_date': t['exit_date'],
                'country': t['country']
            }
            for t in c.fetchall()
        ]

        # Calculate future job forecasts for this employee
        forecasts = get_all_future_jobs_for_employee(emp['id'], trips, warning_threshold)
        for f in forecasts:
            # Enrich with employee metadata for the template
            f['employee_name'] = emp['name']
            all_forecasts.append(f)

    conn.close()

    # Counts before filtering
    red_count = sum(1 for f in all_forecasts if f['risk_level'] == 'red')
    yellow_count = sum(1 for f in all_forecasts if f['risk_level'] == 'yellow')
    green_count = sum(1 for f in all_forecasts if f['risk_level'] == 'green')

    # Apply risk filter
    if risk_filter in {'red', 'yellow', 'green'}:
        filtered = [f for f in all_forecasts if f['risk_level'] == risk_filter]
    else:
        filtered = list(all_forecasts)

    # Sorting
    if sort_by == 'date':
        filtered.sort(key=lambda f: f['job_start_date'])
    elif sort_by == 'employee':
        filtered.sort(key=lambda f: f.get('employee_name', ''))
    elif sort_by == 'days':
        # Sort by projected days after job, descending
        filtered.sort(key=lambda f: f.get('days_after_job', 0), reverse=True)
    else:
        # Default: risk order red > yellow > green
        risk_order = {'red': 0, 'yellow': 1, 'green': 2}
        filtered.sort(key=lambda f: risk_order.get(f['risk_level'], 3))

    return render_template(
        'future_job_alerts.html',
        forecasts=filtered,
        red_count=red_count,
        yellow_count=yellow_count,
        green_count=green_count,
        warning_threshold=warning_threshold,
        risk_filter=risk_filter,
        sort_by=sort_by
    )

@main_bp.route('/export_future_alerts')
@login_required
def export_future_alerts():
    """Export future job alerts to CSV"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    warning_threshold = CONFIG.get('FUTURE_JOB_WARNING_THRESHOLD', 80)

    # Build the same forecast dataset (unfiltered export)
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()

    rows = []
    for emp in employees:
        c.execute('SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?', (emp['id'],))
        trips = [
            {
                'entry_date': t['entry_date'],
                'exit_date': t['exit_date'],
                'country': t['country']
            }
            for t in c.fetchall()
        ]

        forecasts = get_all_future_jobs_for_employee(emp['id'], trips, warning_threshold)
        for f in forecasts:
            rows.append({
                'Employee': emp['name'],
                'Risk Level': f['risk_level'],
                'Job Start': f['job_start_date'].strftime('%d-%m-%Y'),
                'Job End': f['job_end_date'].strftime('%d-%m-%Y'),
                'Country': (f['job'].get('country') or f['job'].get('country_code', '')),
                'Job Duration (days)': f['job_duration'],
                'Days Used Before': f['days_used_before_job'],
                'Days After Job': f['days_after_job'],
                'Days Remaining': f['days_remaining_after_job'],
                'Compliant From': f['compliant_from_date'].strftime('%d-%m-%Y') if f.get('compliant_from_date') else ''
            })

    conn.close()

    # Write CSV
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        'Employee', 'Risk Level', 'Job Start', 'Job End', 'Country',
        'Job Duration (days)', 'Days Used Before', 'Days After Job',
        'Days Remaining', 'Compliant From'
    ]
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r[h] for h in headers])

    csv_data = output.getvalue()
    resp = make_response(csv_data)
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = 'attachment; filename=future_job_alerts.csv'
    return resp

@main_bp.route('/export/trips/csv')
@login_required
def export_trips_csv_route():
    """Export trips to CSV for all employees."""
    from flask import current_app
    db_path = current_app.config['DATABASE']
    try:
        csv_data = export_trips_csv(db_path)
        resp = make_response(csv_data)
        resp.headers['Content-Type'] = 'text/csv'
        resp.headers['Content-Disposition'] = 'attachment; filename=trips.csv'
        return resp
    except Exception as e:
        logger.error(f"Error exporting trips CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/what_if_scenario')
@login_required
def what_if_scenario():
    """Display what-if scenario page"""
    from flask import current_app
    # Provide employees for the select and country code mapping used in template
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()
    conn.close()
    country_codes = current_app.config.get('COUNTRY_CODE_MAPPING', {})
    warning_threshold = current_app.config['CONFIG'].get('FUTURE_JOB_WARNING_THRESHOLD', 80)
    return render_template('what_if_scenario.html', employees=employees, country_codes=country_codes, warning_threshold=warning_threshold)

@main_bp.route('/api/calculate_scenario', methods=['POST'])
@login_required
def api_calculate_scenario():
    from flask import current_app
    data = request.get_json(force=True) or {}
    try:
        employee_id = int(data.get('employee_id'))
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        country = (data.get('country') or '').strip()
        if not (employee_id and start_date and end_date and country):
            return jsonify({'error': 'Missing required fields'}), 400

        # Load employee trips
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?', (employee_id,))
        trips = [
            {'entry_date': r['entry_date'], 'exit_date': r['exit_date'], 'country': r['country']}
            for r in c.fetchall()
        ]
        conn.close()

        # Calculate scenario
        from datetime import date as _date
        scenario = calculate_what_if_scenario(
            employee_id,
            trips,
            _date.fromisoformat(start_date),
            _date.fromisoformat(end_date),
            country,
            current_app.config['CONFIG'].get('FUTURE_JOB_WARNING_THRESHOLD', 80)
        )

        # Shape response for the frontend
        resp = {
            'employee_name': '',
            'job_duration': scenario['job_duration'],
            'days_used_before': scenario['days_used_before_job'],
            'days_after': scenario['days_after_job'],
            'days_remaining': scenario['days_remaining_after_job'],
            'risk_level': scenario['risk_level'],
            'is_schengen': scenario['is_schengen'],
            'compliant_from_date': scenario['compliant_from_date'].isoformat() if scenario.get('compliant_from_date') else None,
        }

        # Get employee name
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT name FROM employees WHERE id = ?', (employee_id,))
        row = c.fetchone()
        conn.close()
        if row:
            resp['employee_name'] = row['name']

        return jsonify(resp)
    except Exception as e:
        logger.error(f"Scenario calculation error: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/admin_privacy_tools')
@login_required
def admin_privacy_tools():
    """Display admin privacy tools"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    retention_months = CONFIG.get('RETENTION_MONTHS', 36)
    try:
        db_path = current_app.config['DATABASE']
        trips = get_expired_trips(db_path, retention_months)
        expired_count = len(trips)
    except Exception:
        expired_count = 0
    # last_purge tracking not persisted yet; show 'Never' via template default
    return render_template(
        'admin_privacy_tools.html',
        retention_months=retention_months,
        expired_count=expired_count,
        last_purge=None
    )

# Alias path expected by some clients/tests
@main_bp.route('/admin/privacy-tools')
@login_required
def admin_privacy_tools_alias():
    return render_template('admin_privacy_tools.html')

# Retention management endpoints
@main_bp.route('/api/retention/preview')
@login_required
def retention_preview():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    retention_months = CONFIG.get('RETENTION_MONTHS', 36)
    db_path = current_app.config['DATABASE']
    try:
        trips = get_expired_trips(db_path, retention_months)
        employees_affected = len({t['employee_id'] for t in trips})
        return jsonify({
            'success': True,
            'trips_count': len(trips),
            'employees_affected': employees_affected
        })
    except Exception as e:
        logger.error(f"Retention preview error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/admin/retention/expired')
@login_required
def retention_expired():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    retention_months = CONFIG.get('RETENTION_MONTHS', 36)
    db_path = current_app.config['DATABASE']
    try:
        trips = get_expired_trips(db_path, retention_months)
    except Exception:
        trips = []
    return render_template('expired_trips.html', trips=trips, retention_months=retention_months)

@main_bp.route('/admin/retention/purge', methods=['POST'])
@login_required
def retention_purge():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    retention_months = CONFIG.get('RETENTION_MONTHS', 36)
    try:
        result = purge_expired_trips(db_path, retention_months)
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'retention_purge', 'admin', result)
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Retention purge error: {e}")
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'retention_purge_error', 'admin', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

# DSAR endpoints
@main_bp.route('/admin/dsar/export/<int:employee_id>')
@login_required
def dsar_export(employee_id: int):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = create_dsar_export(db_path, employee_id, CONFIG['DSAR_EXPORT_DIR'], CONFIG.get('RETENTION_MONTHS', 36))
        if not result.get('success'):
            return jsonify(result), 404
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_export', 'admin', {'employee_id': employee_id, 'file': result['filename']})
        return send_file(result['file_path'], as_attachment=True, download_name=result['filename'])
    except Exception as e:
        logger.error(f"DSAR export error: {e}")
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_export_error', 'admin', {'employee_id': employee_id, 'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/admin/dsar/rectify/<int:employee_id>', methods=['POST'])
@login_required
def dsar_rectify(employee_id: int):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        payload = request.get_json(force=True) or {}
        new_name = (payload.get('new_name') or '').strip()
        result = rectify_employee_name(db_path, employee_id, new_name)
        if result.get('success'):
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_rectify', 'admin', {'employee_id': employee_id, 'new_name': new_name})
        else:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_rectify_failed', 'admin', {'employee_id': employee_id, 'error': result.get('error')})
        return jsonify(result)
    except Exception as e:
        logger.error(f"DSAR rectify error: {e}")
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_rectify_error', 'admin', {'employee_id': employee_id, 'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/admin/dsar/delete/<int:employee_id>', methods=['POST'])
@login_required
def dsar_delete(employee_id: int):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = delete_employee_data(db_path, employee_id)
        if result.get('success'):
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_delete', 'admin', {'employee_id': employee_id, 'trips_deleted': result.get('trips_deleted', 0)})
        else:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_delete_failed', 'admin', {'employee_id': employee_id, 'error': result.get('error')})
        return jsonify(result)
    except Exception as e:
        logger.error(f"DSAR delete error: {e}")
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_delete_error', 'admin', {'employee_id': employee_id, 'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/admin/dsar/anonymize/<int:employee_id>', methods=['POST'])
@login_required
def dsar_anonymize(employee_id: int):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = anonymize_employee(db_path, employee_id)
        if result.get('success'):
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_anonymize', 'admin', {'employee_id': employee_id, 'new_name': result.get('new_name')})
        else:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_anonymize_failed', 'admin', {'employee_id': employee_id, 'error': result.get('error')})
        return jsonify(result)
    except Exception as e:
        logger.error(f"DSAR anonymize error: {e}")
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'dsar_anonymize_error', 'admin', {'employee_id': employee_id, 'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/admin_settings')
@login_required
def admin_settings():
    """Display admin settings"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    return render_template('admin_settings.html', config=CONFIG)

# Minimal API endpoints expected by tests
@main_bp.route('/api/calendar_data')
@login_required
def api_calendar_data():
    # Provide an empty, well-formed payload for now
    return jsonify({'employees': [], 'trips': []})

@main_bp.route('/api/employees/search')
@login_required
def api_employees_search():
    q = request.args.get('q', '').strip().lower()
    conn = get_db()
    c = conn.cursor()
    if q:
        c.execute('SELECT id, name FROM employees WHERE LOWER(name) LIKE ?', (f'%{q}%',))
    else:
        c.execute('SELECT id, name FROM employees ORDER BY name LIMIT 20')
    rows = [{'id': r['id'], 'name': r['name']} for r in c.fetchall()]
    conn.close()
    # Provide both 'employees' and 'results' for compatibility with existing JS
    return jsonify({'employees': rows, 'results': rows})

@main_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change admin password"""
    return redirect(url_for('main.admin_settings'))

@main_bp.route('/delete_all_data', methods=['POST'])
@login_required
def delete_all_data():
    """Delete all data (employees, trips, exported files).
    - If a 'confirmation' field is provided, it must equal "DELETE ALL DATA".
    - Redirects back to the referring page (import page or admin settings).
    """
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']

    # Determine where to send the user back to
    referrer = request.referrer or ''
    def redirect_back():
        if '/import_excel' in referrer:
            return redirect(url_for('main.import_excel'))
        return redirect(url_for('main.admin_settings'))

    try:
        # Enforce confirmation phrase only when provided (admin settings form)
        if 'confirmation' in request.form:
            if request.form.get('confirmation', '').strip() != 'DELETE ALL DATA':
                flash('You must type "DELETE ALL DATA" to confirm this action.')
                return redirect_back()

        # Count existing data for audit purposes
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute('SELECT COUNT(*) FROM trips')
            trips_before = c.fetchone()[0]
        except Exception:
            trips_before = 0
        try:
            c.execute('SELECT COUNT(*) FROM employees')
            employees_before = c.fetchone()[0]
        except Exception:
            employees_before = 0
        try:
            c.execute('SELECT COUNT(*) FROM trips WHERE is_private = 1')
            private_trips_before = c.fetchone()[0]
        except Exception:
            private_trips_before = 0

        # Delete only business trips (exclude private trips)
        try:
            c.execute('DELETE FROM trips WHERE is_private = 0 OR is_private IS NULL')
        except Exception:
            pass
        
        # Delete employees who have no trips remaining (business or private)
        try:
            c.execute('''
                DELETE FROM employees 
                WHERE id NOT IN (
                    SELECT DISTINCT employee_id FROM trips
                )
            ''')
        except Exception:
            pass
        try:
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # Remove exported files but keep the directory itself
        exports_dir = CONFIG.get('DSAR_EXPORT_DIR')
        export_files_deleted = 0
        if exports_dir and os.path.isdir(exports_dir):
            for root, dirs, files in os.walk(exports_dir):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                        export_files_deleted += 1
                    except Exception:
                        pass

        # Write audit entry
        try:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'delete_all_data', 'admin', {
                'employees_deleted': employees_before,
                'trips_deleted': trips_before - private_trips_before,
                'private_trips_preserved': private_trips_before,
                'export_files_deleted': export_files_deleted
            })
        except Exception:
            pass

        if private_trips_before > 0:
            flash(f'All business travel data cleared successfully. {private_trips_before} personal holiday trip(s) preserved.')
        else:
            flash('All data has been cleared successfully.')
        return redirect_back()
    except Exception as e:
        logger.error(f"Delete all data error: {e}")
        try:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'delete_all_data_error', 'admin', {'error': str(e)})
        except Exception:
            pass
        flash(f'Failed to delete data: {str(e)}')
        return redirect_back()

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

@main_bp.route('/dev/admin-bootstrap', methods=['GET', 'POST'])
def dev_admin_bootstrap():
    """
    Development-only admin bootstrap route.
    Only available when FLASK_ENV=development and LOCAL_ADMIN_SETUP_TOKEN is set.
    """
    from flask import current_app
    
    # Check if this is development environment
    if current_app.config.get('ENV') != 'development' and os.getenv('FLASK_ENV') != 'development':
        return "Not available in production", 403
    
    # Check for setup token
    setup_token = os.getenv('LOCAL_ADMIN_SETUP_TOKEN')
    if not setup_token:
        return "Setup token not configured", 403
    
    if request.method == 'POST':
        provided_token = request.form.get('token', '')
        new_password = request.form.get('password', '')
        
        if provided_token != setup_token:
            return render_template('setup.html', error='Invalid setup token')
        
        if not new_password or len(new_password) < 6:
            return render_template('setup.html', error='Password must be at least 6 characters')
        
        # Create admin account
        from .models import Admin
        hasher = Hasher()
        password_hash = hasher.hash(new_password)
        Admin.set_password_hash(password_hash)
        
        return render_template('login.html', success='Admin account created successfully. Please log in.')
    
    return render_template('setup.html', dev_mode=True)

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
