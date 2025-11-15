from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_file
import hashlib
import sqlite3
import logging
import traceback
from datetime import datetime, timedelta, date
import os
import re
from pathlib import Path
from typing import Optional
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
from .runtime_env import build_runtime_state
from .middleware.auth import login_required, current_user

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

# Rate limiting for login attempts (legacy /dev route)
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5 minutes

def get_db():
    """Get database connection"""
    from flask import current_app
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def _current_actor(default: str = 'admin') -> str:
    """Return the username for audit logging."""
    user = current_user()
    if user and getattr(user, 'username', None):
        return user.username  # type: ignore[attr-defined]
    return default

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
    try:
        from flask import current_app
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls'})
    except (RuntimeError, KeyError):
        # Fallback if app context not available or config missing
        allowed_extensions = {'xlsx', 'xls'}
    
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

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

@main_bp.route('/privacy-policy')
def privacy_policy():
    """Alias for /privacy route for consistency"""
    from flask import redirect, url_for
    return redirect(url_for('main.privacy'))

@main_bp.route('/cookie-policy')
def cookie_policy():
    """Cookie policy page explaining cookie usage"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    return render_template('cookie_policy.html',
                         current_date=datetime.now().strftime('%Y-%m-%d'))

# Calendar Feature - In Development
# Accessible only when CALENDAR_DEV_MODE is enabled or in development environment
def _is_calendar_enabled():
    """Check if calendar feature should be accessible (dev mode only)"""
    from flask import current_app
    import os
    
    # Check config flag
    config = current_app.config.get('CONFIG', {})
    if config.get('CALENDAR_DEV_MODE', False):
        return True
    
    # Check environment variable
    if os.getenv('CALENDAR_DEV_MODE', '').lower() in ('true', '1', 'yes'):
        return True
    
    # Check if in development environment (not production)
    is_production = (
        os.getenv('FLASK_ENV') == 'production' or 
        os.getenv('RENDER') == 'true' or
        os.getenv('RENDER_EXTERNAL_HOSTNAME')
    )
    return not is_production  # Available in non-production environments

@main_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view - only accessible in development mode"""
    if not _is_calendar_enabled():
        return '<html><body><h1>Calendar Unavailable</h1><p>This feature is currently in development and not available in production.</p><p>For development access, set CALENDAR_DEV_MODE=true in your environment or config.</p></body></html>', 403
    
    from flask import current_app
    from datetime import date, timedelta
    
    # Get config for template
    config = current_app.config.get('CONFIG', {})
    
    # Optional: Get employee filter from query params
    employee_id = request.args.get('employee_id', type=int)
    employee_name = None
    
    if employee_id:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        employee = c.fetchone()
        conn.close()
        
        if employee:
            employee_name = employee['name']
    
    return render_template('calendar.html',
                         employee_id=employee_id,
                         employee_name=employee_name,
                         config={'CONFIG': config})

@main_bp.route('/calendar_dev')
@login_required
def calendar_dev():
    """Development-only calendar access route"""
    if not _is_calendar_enabled():
        return '<html><body><h1>Development Access Only</h1><p>This route is only available in development mode.</p></body></html>', 403
    return redirect(url_for('main.calendar'))

@main_bp.route('/calendar_view')
@login_required
def calendar_view():
    """Redirect to calendar (if enabled)"""
    if not _is_calendar_enabled():
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.calendar'))

# @main_bp.route('/employee/<int:employee_id>/calendar')
# @login_required
# def employee_calendar(employee_id):
#     """Employee-specific calendar view"""
#     from flask import current_app
#
#     # Verify employee exists
#     conn = get_db()
#     c = conn.cursor()
#     c.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
#     employee = c.fetchone()
#     conn.close()
#
#     if not employee:
#         flash('Employee not found', 'error')
#         return redirect(url_for('main.dashboard'))
#
#     return render_template('calendar.html', employee_id=employee_id, employee_name=employee['name'])

@main_bp.route('/api/news/refresh', methods=['POST'])
@login_required
def refresh_news():
    """Manually refresh news from all sources."""
    from flask import current_app
    
    try:
        from .services.news_fetcher import fetch_news_from_sources
        db_path = current_app.config['DATABASE']
        
        # Start background refresh
        import threading
        def refresh_news_bg():
            try:
                news_items = fetch_news_from_sources(db_path)
                logger.info(f"Background news refresh completed: {len(news_items)} items")
            except Exception as e:
                logger.error(f"Background news refresh failed: {e}")
        
        thread = threading.Thread(target=refresh_news_bg)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'News refresh started in background'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error starting news refresh: {str(e)}'
        }), 500

# Login route moved to auth_bp - this route disabled to avoid conflicts
# @main_bp.route('/login', methods=['GET', 'POST'])
def login_old():
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
            from app.modules.auth import SessionManager
            SessionManager.set_user(1, 'admin')
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'login_success', 'admin', {'ip': ip})
            return redirect(url_for('main.home'))
        # failed
        conn.close()
        count, first_ts = LOGIN_ATTEMPTS.get(ip, (0, now))
        LOGIN_ATTEMPTS[ip] = (count + 1, first_ts)
        write_audit(CONFIG['AUDIT_LOG_PATH'], 'login_failure', 'admin', {'ip': ip})
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration for new accounts"""
    if request.method == 'POST':
        # Get form data
        company_name = request.form.get('company_name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')
        
        # Validation
        errors = []
        
        if not company_name:
            errors.append('Company name is required')
        if not full_name:
            errors.append('Full name is required')
        if not email:
            errors.append('Email address is required')
        elif '@' not in email:
            errors.append('Please enter a valid email address')
        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if not terms:
            errors.append('You must agree to the terms and conditions')
        
        if errors:
            return render_template('signup.html', error=errors[0])
        
        # Check if admin already exists (for now, only allow one admin)
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM admin WHERE id = 1')
        existing_admin = c.fetchone()
        
        if existing_admin:
            conn.close()
            return render_template('signup.html', error='An admin account already exists. Please contact support for access.')
        
        try:
            # Create new admin account with company info
            hasher = Hasher()
            password_hash = hasher.hash(password)
            
            c.execute('''
                INSERT INTO admin (id, password_hash, company_name, full_name, email, phone, created_at)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            ''', (password_hash, company_name, full_name, email, phone, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            # Log successful signup
            from flask import current_app
            CONFIG = current_app.config['CONFIG']
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'admin_signup', 'system', {
                'company_name': company_name,
                'email': email,
                'full_name': full_name
            })
            
            return render_template('login.html', success='Account created successfully! Please log in with your credentials.')
            
        except Exception as e:
            conn.rollback()
            conn.close()
            logger.error(f"Signup error: {e}")
            return render_template('signup.html', error='An error occurred during registration. Please try again.')
    
    return render_template('signup.html')

@main_bp.route('/get-started')
def get_started():
    """Alias for signup page"""
    return redirect(url_for('main.signup'))

@main_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """First-time setup to create admin account"""
    from .models import Admin
    
    # Check if admin already exists
    if Admin.exists():
        return redirect(url_for('auth.login'))
    
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
    actor = _current_actor()
    from app.modules.auth import SessionManager
    SessionManager.clear_session()
    write_audit(CONFIG['AUDIT_LOG_PATH'], 'logout', actor, {})
    return redirect(url_for('auth.login'))

@main_bp.route('/profile')
@login_required
def profile():
    """Lightweight admin profile placeholder page."""
    user = current_user()
    admin_name = getattr(user, 'username', 'Admin') if user else 'Admin'
    last_login = session.get('last_seen') or session.get('last_activity')
    return render_template('profile.html', admin_name=admin_name, last_login=last_login)

@main_bp.route('/home')
@login_required
def home():
    """Home page with quick info and EU travel news"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    # Check if we should refresh news in background (simplified for performance)
    import os
    if os.getenv('NEWS_FETCH_ENABLED', 'true').lower() == 'true':
        try:
            # Start background news refresh (non-blocking) - simplified check
            import threading
            def refresh_news():
                try:
                    from .services.news_fetcher import fetch_news_from_sources
                    with current_app.app_context():
                        fetch_news_from_sources(current_app.config['DATABASE'])
                except Exception as e:
                    logger.error(f"Background news refresh failed: {e}")
            
            thread = threading.Thread(target=refresh_news)
            thread.daemon = True
            thread.start()
        except Exception as e:
            logger.error(f"Error starting background news refresh: {e}")
    
    # Get admin name if available
    admin_name = 'Admin'
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT full_name FROM admin WHERE id = 1')
        row = c.fetchone()
        if row and row[0]:
            admin_name = row[0].split()[0] if row[0] else 'Admin'  # Use first name only
        conn.close()
    except Exception:
        pass
    
    # Get quick stats
    conn = get_db()
    c = conn.cursor()
    
    # Active employees count
    c.execute('SELECT COUNT(*) FROM employees')
    total_employees = c.fetchone()[0]
    
    # Trips logged this month
    from datetime import date
    this_month = date.today().replace(day=1).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM trips WHERE entry_date >= ?', (this_month,))
    trips_this_month = c.fetchone()[0]
    
    # At risk of 90-day limit (days_remaining < 10) - simplified for performance
    today = date.today()
    at_risk_count = 0
    try:
        # Use a more efficient query to get at-risk count
        c.execute('''
            SELECT COUNT(DISTINCT e.id) 
            FROM employees e
            JOIN trips t ON e.id = t.employee_id
            WHERE t.entry_date >= date('now', '-90 days')
            GROUP BY e.id
            HAVING COUNT(t.id) > 0
        ''')
        # This is a simplified check - for exact rolling90 calculation, 
        # we'd need the full rolling90 service, but this gives a reasonable estimate
        at_risk_count = 0  # Simplified for now - can be enhanced later
    except Exception as e:
        logger.error(f"Error calculating at-risk count: {e}")
        at_risk_count = 0
    
    conn.close()
    
    # Get news (use cached version for performance)
    try:
        from .services.news_fetcher import get_cached_news
        db_path = current_app.config['DATABASE']
        news_items = get_cached_news(db_path)
    except Exception as e:
        logger.error(f"Error fetching cached news: {e}")
        news_items = []
    
    return render_template('home.html',
                         admin_name=admin_name,
                         total_employees=total_employees,
                         trips_this_month=trips_this_month,
                         at_risk_count=at_risk_count,
                         news_items=news_items)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    
    # OPTIMIZATION (Phase 2): Response caching for dashboard
    cache = current_app.config.get('CACHE')
    sort_by = request.args.get('sort', 'first_name')
    cache_key = None
    
    # Generate cache key based on sort parameter and data version
    # Cache key includes sort_by to ensure different sorts are cached separately
    # OPTIMIZATION V2: Single query instead of 2 queries for cache key generation
    if cache:
        # Get a data version indicator (e.g., max trip/employee update timestamp)
        try:
            conn_temp = get_db()
            c_temp = conn_temp.cursor()
            # Get max timestamp from both tables in a single query
            c_temp.execute('''
                SELECT MAX(ts) as max_ts FROM (
                    SELECT MAX(created_at) as ts FROM trips
                    UNION ALL
                    SELECT MAX(created_at) as ts FROM employees
                )
            ''')
            result = c_temp.fetchone()
            max_timestamp = result[0] if result and result[0] else 'default'
            cache_key = f'dashboard:{sort_by}:{max_timestamp}'
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug("Dashboard response served from cache")
                return cached_response
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            cache = None  # Fall back to no caching
    
    try:
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
        
        # Use fixed compliance start date (October 12, 2025)
        from .services.rolling90 import COMPLIANCE_START_DATE
        compliance_start_date = COMPLIANCE_START_DATE
        
        # Track future compliance alerts summary
        future_alerts_red = 0
        future_alerts_yellow = 0
        future_alerts_green = 0

        # OPTIMIZATION: Batch fetch all trips for all employees in a single query
        # This eliminates N+1 query problem (was 4-6 queries per employee, now 1 query total)
        if employees:
            employee_ids = [emp['id'] for emp in employees]
            placeholders = ','.join('?' * len(employee_ids))
            
            # Single query to get all trips for all employees
            c.execute(f'''
                SELECT 
                    employee_id,
                    entry_date,
                    exit_date,
                    country,
                    is_private,
                    id as trip_id
                FROM trips
                WHERE employee_id IN ({placeholders})
                ORDER BY employee_id, entry_date DESC
            ''', employee_ids)
            all_trips_raw = c.fetchall()
            
            # Group trips by employee_id in Python (much faster than multiple DB queries)
            trips_by_employee = {}
            trip_counts_by_employee = {}
            for trip in all_trips_raw:
                emp_id = trip['employee_id']
                if emp_id not in trips_by_employee:
                    trips_by_employee[emp_id] = []
                    trip_counts_by_employee[emp_id] = 0
                trips_by_employee[emp_id].append({
                    'entry_date': trip['entry_date'],
                    'exit_date': trip['exit_date'],
                    'country': trip['country'],
                    'is_private': trip['is_private'],
                    'trip_id': trip['trip_id']
                })
                trip_counts_by_employee[emp_id] += 1
            
            # Get next trips and recent trips in batch queries
            today_str = today.strftime('%Y-%m-%d')
            
            # Batch query for next upcoming trips
            # Use a simpler approach: fetch all future trips and filter in Python
            c.execute(f'''
                SELECT 
                    employee_id,
                    country,
                    entry_date,
                    is_private
                FROM trips
                WHERE entry_date > ? 
                  AND employee_id IN ({placeholders})
                ORDER BY employee_id, entry_date ASC
            ''', [today_str] + employee_ids)
            future_trips_raw = c.fetchall()
            
            # Group by employee and take first (earliest) trip per employee
            next_trips_by_employee = {}
            for trip in future_trips_raw:
                emp_id = trip['employee_id']
                if emp_id not in next_trips_by_employee:
                    next_trips_by_employee[emp_id] = dict(trip)
            
            # Batch query for recent trips (top 5 per employee)
            # Note: SQLite doesn't support window functions easily, so we'll handle this in Python
            # for better performance, we'll fetch recent trips and filter in Python
            c.execute(f'''
                SELECT 
                    employee_id,
                    country,
                    entry_date,
                    exit_date,
                    is_private
                FROM trips
                WHERE employee_id IN ({placeholders})
                ORDER BY employee_id, exit_date DESC
            ''', employee_ids)
            all_recent_trips_raw = c.fetchall()
            
            # Group recent trips by employee (top 5 per employee)
            recent_trips_by_employee = {}
            for trip in all_recent_trips_raw:
                emp_id = trip['employee_id']
                if emp_id not in recent_trips_by_employee:
                    recent_trips_by_employee[emp_id] = []
                if len(recent_trips_by_employee[emp_id]) < 5:
                    recent_trips_by_employee[emp_id].append(dict(trip))
        else:
            trips_by_employee = {}
            trip_counts_by_employee = {}
            next_trips_by_employee = {}
            recent_trips_by_employee = {}

        # Process each employee with pre-fetched data
        for emp in employees:
            emp_id = emp['id']
            
            # Get trips for this employee (already fetched in batch)
            trips = trips_by_employee.get(emp_id, [])
            
            # Calculate presence days and usage using new rolling90 module
            presence = presence_days(trips, compliance_start_date)
            days_used = days_used_in_window(presence, today, compliance_start_date)
            days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)
            risk_level = get_risk_level(days_remaining, risk_thresholds)
            
            # Calculate earliest safe entry date
            safe_entry = earliest_safe_entry(presence, today, compliance_start_date=compliance_start_date)
            
            # Calculate days until compliant for at-risk employees (days_remaining < 0)
            days_until_compliant_val = None
            compliance_date = None
            if days_remaining < 0:
                days_until_compliant_val, compliance_date = days_until_compliant(presence, today, compliance_start_date=compliance_start_date)

            # Get total trip count (already calculated from batch query)
            trip_count = trip_counts_by_employee.get(emp_id, 0)

            # Get next upcoming trip (already fetched in batch)
            next_trip_row = next_trips_by_employee.get(emp_id)
            next_trip = redact_private_trip_data(next_trip_row) if next_trip_row else None

            # Get recent trips (already fetched in batch)
            recent_trips_raw = recent_trips_by_employee.get(emp_id, [])
            recent_trips = [redact_private_trip_data(dict(trip)) for trip in recent_trips_raw]
            
            # Calculate future job forecasts for this employee
            forecasts = get_all_future_jobs_for_employee(emp_id, trips, warning_threshold, compliance_start_date)
            for forecast in forecasts:
                if forecast['risk_level'] == 'red':
                    future_alerts_red += 1
                elif forecast['risk_level'] == 'yellow':
                    future_alerts_yellow += 1
                else:
                    future_alerts_green += 1
            
            forecast_reference = forecasts[0] if forecasts else None
            if forecast_reference:
                projected_remaining = forecast_reference.get('days_remaining_after_job', days_remaining)
                projected_risk = forecast_reference.get('risk_level', risk_level)
            else:
                projected_remaining = days_remaining
                projected_risk = risk_level
            
            # Create employee data object
            emp_data = {
                'id': emp['id'],
                'name': emp['name'],
                'days_used': days_used,
                'days_remaining': days_remaining,
                'risk_level': risk_level,
                'forecasted_days_remaining': projected_remaining,
                'forecast_risk_level': projected_risk,
                'forecast_reference': forecast_reference,
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
        
        # Get future job alerts summary
        future_alerts_summary = {
            'red': future_alerts_red,
            'yellow': future_alerts_yellow,
            'green': future_alerts_green
        }
        
        response = render_template('dashboard.html', 
                             employees=employee_data, 
                             at_risk_employees=at_risk_employees,
                             future_alerts_summary=future_alerts_summary,
                             sort_by=sort_by,
                             risk_thresholds=risk_thresholds)
        
        # OPTIMIZATION (Phase 2): Cache the response for 60 seconds
        if cache:
            try:
                cache.set(cache_key, response, timeout=60)
                logger.debug("Dashboard response cached")
            except Exception as e:
                logger.warning(f"Failed to cache dashboard response: {e}")
        
        return response
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading the dashboard. Please try again.', 'error')
        return render_template('dashboard.html', 
                             employees=[], 
                             at_risk_employees=[],
                             future_alerts_summary={'red': 0, 'yellow': 0, 'green': 0},
                             sort_by='first_name',
                             risk_thresholds={'green': 30, 'amber': 10})
    # Connection managed by Flask teardown handler in models.py

@main_bp.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {'green': 30, 'amber': 10})
    
    # Use fixed compliance start date (October 12, 2025)
    from .services.rolling90 import COMPLIANCE_START_DATE
    compliance_start_date = COMPLIANCE_START_DATE
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get employee details
        # OPTIMIZATION V2: Select specific columns instead of SELECT *
        # Note: created_at may not exist in all database schemas
        try:
            c.execute('SELECT id, name, created_at FROM employees WHERE id = ?', (employee_id,))
        except sqlite3.OperationalError:
            # Fallback if created_at column doesn't exist
            c.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        employee = c.fetchone()
        if not employee:
            return "Employee not found", 404
        
        # Get all trips for this employee
        # OPTIMIZATION V2: Select specific columns instead of SELECT *
        c.execute('SELECT id, employee_id, entry_date, exit_date, country, purpose, job_ref, ghosted, travel_days, is_private FROM trips WHERE employee_id = ? ORDER BY entry_date ASC', (employee_id,))
        rows = c.fetchall()
        # Debug: Log trip count for troubleshooting
        logger.debug(f"Employee {employee_id}: Found {len(rows)} trips in database")

        # Build trip dicts and compute durations/statuses
        from datetime import date as _date
        today = _date.today()
        trips_list = []
        simple_trips = []  # for rolling90
        trip_date_meta = {}
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
            trip_date_meta[row['id']] = {
                'entry': entry_dt,
                'exit': exit_dt
            }
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
        presence = presence_days(simple_trips, compliance_start_date)
        from datetime import datetime as _dt
        ref_date = today
        days_used = days_used_in_window(presence, ref_date, compliance_start_date)
        days_remaining = calculate_days_remaining(presence, ref_date, compliance_start_date=compliance_start_date)
        risk_level = get_risk_level(days_remaining, risk_thresholds)
        safe_entry = earliest_safe_entry(presence, ref_date, compliance_start_date=compliance_start_date)
        days_until_safe = None
        compliant_date = None
        if days_remaining < 0:
            days_until_safe, compliant_date = days_until_compliant(presence, ref_date, compliance_start_date=compliance_start_date)

        # Calculate per-trip compliance snapshots so job context rows reflect accurate rolling totals.
        limit = 90
        trip_metrics = {}
        for trip_id, meta in trip_date_meta.items():
            baseline = meta.get('exit') or meta.get('entry') or today
            ref_point = baseline + timedelta(days=1)
            remaining_after_trip = calculate_days_remaining(presence, ref_point, compliance_start_date=compliance_start_date)
            trip_metrics[trip_id] = {
                'days_remaining_after': remaining_after_trip,
                'days_used_to_date': limit - remaining_after_trip,
                'risk_level_after': get_risk_level(remaining_after_trip, risk_thresholds)
            }

        # Annotate per-trip display fields with the computed metrics, falling back to current snapshot.
        for t in trips_list:
            metrics = trip_metrics.get(t['id'])
            if metrics:
                t['days_remaining_after'] = metrics['days_remaining_after']
                t['risk_level_after'] = metrics['risk_level_after']
                t['days_used_to_date'] = metrics['days_used_to_date']
            else:
                t['days_remaining_after'] = days_remaining
                t['risk_level_after'] = risk_level
                t['days_used_to_date'] = days_used

        # Debug: Log trip count being passed to template
        logger.debug(f"Employee {employee_id}: Passing {len(trips_list)} trips to template")
        
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
    
    except Exception as e:
        logger.error(f"Employee detail error for employee {employee_id}: {e}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading employee details. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
    finally:
        if 'conn' in locals():
            conn.close()

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
        from .models import get_db
        conn = get_db()
        c = conn.cursor()
        
        # Delete all trips for this employee
        c.execute('DELETE FROM trips WHERE employee_id = ?', (employee_id,))
        trips_deleted = c.rowcount
        
        # Delete the employee
        c.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
        employee_deleted = c.rowcount
        
        conn.commit()
        
        if employee_deleted > 0:
            flash(f'Employee and {trips_deleted} associated trip(s) deleted successfully.', 'success')
            # Write audit log
            try:
                from flask import current_app
                CONFIG = current_app.config.get('CONFIG', {})
                audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
                write_audit(audit_log_path, 'employee_delete', _current_actor(), {
                    'employee_id': employee_id,
                    'trips_deleted': trips_deleted
                })
            except Exception:
                pass  # Don't fail delete if audit logging fails
        else:
            flash('Employee not found.', 'error')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        flash(f'Error deleting employee: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

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
        
        # OPTIMIZATION (Phase 2): Invalidate dashboard cache after trip addition
        try:
            from .utils.cache_invalidation import invalidate_dashboard_cache
            invalidate_dashboard_cache()
        except Exception as e:
            logger.warning(f"Failed to invalidate cache after trip addition: {e}")
        
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
        # OPTIMIZATION V2: Select specific columns instead of SELECT *
        c.execute('SELECT id, employee_id, entry_date, exit_date, country FROM trips WHERE id = ?', (trip_id,))
        trip = c.fetchone()
        
        if not trip:
            return jsonify({'success': False, 'error': 'Trip not found'})
        
        c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        conn.commit()
        
        # OPTIMIZATION (Phase 2): Invalidate dashboard cache after trip deletion
        try:
            from .utils.cache_invalidation import invalidate_dashboard_cache
            invalidate_dashboard_cache()
        except Exception as e:
            logger.warning(f"Failed to invalidate cache after trip deletion: {e}")
        
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
        # Support both JSON and form data
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = request.get_json() or {}
            except Exception as e:
                logger.error(f"Failed to parse JSON in edit_trip: {e}")
                payload = {}
        else:
            payload = request.form.to_dict() if request.form else {}
        
        new_country = (payload.get('country') or payload.get('country_code') or '').strip()
        new_entry = payload.get('entry_date')
        new_exit = payload.get('exit_date')
        new_employee_id = payload.get('employee_id')  # NEW: Support employee changes

        if not (new_country and new_entry and new_exit):
            return jsonify({'success': False, 'message': 'Missing required fields', 'error': 'Missing required fields'}), 400

        # Parse dates
        from datetime import date as _date
        try:
            entry_dt = _date.fromisoformat(new_entry)
            exit_dt = _date.fromisoformat(new_exit)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400

        # Load existing trip and employee
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, employee_id FROM trips WHERE id = ?', (trip_id,))
        current_trip = c.fetchone()
        if not current_trip:
            conn.close()
            return jsonify({'success': False, 'error': 'Trip not found'}), 404

        # Determine target employee (could be same or different)
        target_employee_id = int(new_employee_id) if new_employee_id else current_trip['employee_id']

        # Validate new employee exists if changing employee
        if new_employee_id and int(new_employee_id) != current_trip['employee_id']:
            c.execute('SELECT id FROM employees WHERE id = ?', (target_employee_id,))
            if not c.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Target employee not found'}), 400

        # Validate against overlaps for target employee
        c.execute('SELECT id, entry_date, exit_date FROM trips WHERE employee_id = ? AND id != ?',
                 (target_employee_id, trip_id))
        existing = [{'id': r['id'], 'entry_date': r['entry_date'], 'exit_date': r['exit_date']}
                   for r in c.fetchall()]

        hard_errors, _warnings = validate_trip(existing, entry_dt, exit_dt, trip_id_to_exclude=trip_id)
        if hard_errors:
            conn.close()
            return jsonify({'success': False, 'error': hard_errors[0]}), 400

        # Update trip (potentially with new employee)
        c.execute('UPDATE trips SET employee_id = ?, country = ?, entry_date = ?, exit_date = ? WHERE id = ?',
                 (target_employee_id, new_country, new_entry, new_exit, trip_id))
        conn.commit()

        try:
            write_audit(CONFIG['AUDIT_LOG_PATH'], 'trip_updated', 'admin', {
                'trip_id': trip_id,
                'old_employee_id': current_trip['employee_id'],
                'new_employee_id': target_employee_id,
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
    CONFIG = current_app.config.get('CONFIG', {})
    runtime_state = build_runtime_state()
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', runtime_state.directories['uploads']))
    upload_dir.mkdir(parents=True, exist_ok=True)

    logger.info("import_excel: %s request (upload_dir=%s)", request.method, upload_dir)

    if request.method == 'POST':
        start_time = time.monotonic()
        uploaded_path: Optional[Path] = None
        db_conn: Optional[sqlite3.Connection] = None
        filename = None

        try:
            file = request.files.get('excel_file')
            if not file or file.filename == '':
                flash('Please choose an Excel file to upload.', 'warning')
                return make_response(render_template('import_excel.html'), 400)

            if not allowed_file(file.filename):
                flash('Invalid file type. Only .xlsx and .xls files are accepted.', 'warning')
                return make_response(render_template('import_excel.html'), 400)

            filename = secure_filename(file.filename)
            if not filename:
                flash('The uploaded file name is invalid.', 'warning')
                return make_response(render_template('import_excel.html'), 400)

            uploaded_path = upload_dir / filename
            file.save(uploaded_path)
            if not uploaded_path.exists():
                raise FileNotFoundError(f"Uploaded file missing after save: {uploaded_path}")

            import sys
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from importer import import_excel as process_excel  # Lazy import to ensure latest version

            from .models import get_db
            db_conn = get_db()

            result = process_excel(str(uploaded_path), enable_extended_scan=True, db_conn=db_conn)
            elapsed = time.monotonic() - start_time
            logger.info("Finished Excel processing for '%s' in %.2fs", filename, elapsed)

            audit_payload = {
                'filename': filename,
                'elapsed_seconds': round(elapsed, 2),
                'database': current_app.config.get('DATABASE'),
            }

            if result.get('success'):
                audit_payload.update({
                    'trips_added': result.get('trips_added', 0),
                    'employees_processed': result.get('employees_processed', 0),
                    'warnings': result.get('warnings', []),
                })
                try:
                    write_audit(CONFIG.get('AUDIT_LOG_PATH', str(runtime_state.audit_log_file)),
                                'excel_import_success', 'admin', audit_payload)
                except Exception as audit_err:
                    logger.warning("Failed to write audit log: %s", audit_err)

                if result.get('warnings'):
                    flash('Import completed with warnings. Review the summary below.', 'warning')
                else:
                    flash('Excel file imported successfully.', 'success')

                response = render_template('import_excel.html', import_summary=result)
                return make_response(response, 200)

            error_message = result.get('error', 'Unknown error')
            error_details = result.get('details')
            status_code = 400 if error_details else 500

            logger.error("Excel import failed (%s): %s | details=%s", filename, error_message, error_details)
            try:
                write_audit(CONFIG.get('AUDIT_LOG_PATH', str(runtime_state.audit_log_file)),
                            'excel_import_failed', 'admin',
                            {**audit_payload, 'error': error_message, 'details': error_details})
            except Exception as audit_err:
                logger.warning("Failed to write audit log: %s", audit_err)

            user_message = error_message
            if error_details:
                row = error_details.get('row')
                column = error_details.get('column')
                if row or column:
                    user_message += f" (Row {row or '?'} Column {column or '?'})"
            flash(user_message, 'danger')
            return make_response(render_template('import_excel.html', import_error=result), status_code)

        except Exception as exc:
            logger.error("Error processing Excel file '%s': %s", filename, exc)
            logger.error(traceback.format_exc())
            try:
                write_audit(
                    CONFIG.get('AUDIT_LOG_PATH', str(runtime_state.audit_log_file)),
                    'excel_import_error',
                    'admin',
                    {
                        'filename': filename or 'unknown',
                        'error': str(exc),
                    },
                )
            except Exception as audit_err:
                logger.warning("Failed to write audit log: %s", audit_err)

            flash('An unexpected error occurred while processing the Excel file. Please try again.', 'danger')
            return make_response(render_template('import_excel.html'), 500)

        finally:
            if db_conn:
                try:
                    db_conn.close()
                except Exception:
                    pass
            if uploaded_path and uploaded_path.exists():
                try:
                    uploaded_path.unlink()
                except Exception as cleanup_err:
                    logger.warning("Failed to delete uploaded file %s: %s", uploaded_path, cleanup_err)

    return render_template('import_excel.html')


@main_bp.route('/future_job_alerts')
@login_required
def future_job_alerts():
    """Display future job alerts"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']

    warning_threshold = CONFIG.get('FUTURE_JOB_WARNING_THRESHOLD', 80)
    
    # Use fixed compliance start date (October 12, 2025)
    from .services.rolling90 import COMPLIANCE_START_DATE
    compliance_start_date = COMPLIANCE_START_DATE

    # Query params
    risk_filter = request.args.get('risk', 'all')  # all | red | yellow | green
    sort_by = request.args.get('sort', 'risk')     # risk | date | employee | days

    # Collect forecasts across all employees
    # OPTIMIZATION V2: Batch fetch all trips instead of N queries (one per employee)
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()

    all_forecasts = []
    
    if employees:
        # Batch fetch all trips for all employees in a single query
        employee_ids = [emp['id'] for emp in employees]
        placeholders = ','.join('?' * len(employee_ids))
        
        c.execute(f'''
            SELECT employee_id, entry_date, exit_date, country
            FROM trips
            WHERE employee_id IN ({placeholders})
            ORDER BY employee_id, entry_date ASC
        ''', employee_ids)
        
        all_trips_raw = c.fetchall()
        
        # Group trips by employee_id in Python (much faster than multiple DB queries)
        trips_by_employee = {}
        for trip in all_trips_raw:
            emp_id = trip['employee_id']
            if emp_id not in trips_by_employee:
                trips_by_employee[emp_id] = []
            trips_by_employee[emp_id].append({
                'entry_date': trip['entry_date'],
                'exit_date': trip['exit_date'],
                'country': trip['country']
            })
        
        # Process forecasts for each employee
        for emp in employees:
            trips = trips_by_employee.get(emp['id'], [])
            
            # Calculate future job forecasts for this employee
            forecasts = get_all_future_jobs_for_employee(emp['id'], trips, warning_threshold, compliance_start_date)
            for f in forecasts:
                # Enrich with employee metadata for the template
                f['employee_name'] = emp['name']
                all_forecasts.append(f)
    
    # Connection managed by Flask teardown handler

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
    
    # Use fixed compliance start date (October 12, 2025)
    from .services.rolling90 import COMPLIANCE_START_DATE
    compliance_start_date = COMPLIANCE_START_DATE

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

        forecasts = get_all_future_jobs_for_employee(emp['id'], trips, warning_threshold, compliance_start_date)
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

@main_bp.route('/admin_settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Display admin settings and handle form submission"""
    from flask import current_app, request, flash, redirect, url_for
    CONFIG = current_app.config['CONFIG']
    
    if request.method == 'POST':
        try:
            # Update configuration values
            config_updates = {}
            
            # Data Retention
            if 'retention_months' in request.form:
                config_updates['RETENTION_MONTHS'] = int(request.form['retention_months'])
            
            # Session Settings
            if 'session_timeout' in request.form:
                config_updates['SESSION_IDLE_TIMEOUT_MINUTES'] = int(request.form['session_timeout'])
            
            if 'session_cookie_secure' in request.form:
                config_updates['SESSION_COOKIE_SECURE'] = True
            else:
                config_updates['SESSION_COOKIE_SECURE'] = False
            
            # Password Settings
            if 'password_scheme' in request.form:
                config_updates['PASSWORD_HASH_SCHEME'] = request.form['password_scheme']
            
            # Export Settings
            if 'export_dir' in request.form:
                config_updates['DSAR_EXPORT_DIR'] = request.form['export_dir']
            
            if 'audit_log' in request.form:
                config_updates['AUDIT_LOG_PATH'] = request.form['audit_log']
            
            # Future Job Compliance
            if 'warning_threshold' in request.form:
                config_updates['FUTURE_JOB_WARNING_THRESHOLD'] = int(request.form['warning_threshold'])
            
            # Risk Level Thresholds
            if 'risk_threshold_green' in request.form and 'risk_threshold_amber' in request.form:
                risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {})
                risk_thresholds['green'] = int(request.form['risk_threshold_green'])
                risk_thresholds['amber'] = int(request.form['risk_threshold_amber'])
                config_updates['RISK_THRESHOLDS'] = risk_thresholds
            
            # News Filter Region
            if 'news_filter_region' in request.form:
                config_updates['NEWS_FILTER_REGION'] = request.form['news_filter_region']
            
            # Update the configuration
            if config_updates:
                CONFIG.update(config_updates)
                # Save configuration to file
                import json
                import re
                with open('config.py', 'r') as f:
                    content = f.read()
                
                # Update the configuration values in the file
                for key, value in config_updates.items():
                    if key == 'RISK_THRESHOLDS':
                        content = re.sub(
                            rf'{key}\s*=\s*{{[^}}]*}}',
                            f'{key} = {value}',
                            content
                        )
                    else:
                        content = re.sub(
                            rf'{key}\s*=\s*[^\n]*',
                            f'{key} = {repr(value)}',
                            content
                        )
                
                with open('config.py', 'w') as f:
                    f.write(content)
                
                flash('Settings updated successfully!', 'success')
            else:
                flash('No changes were made.', 'info')
                
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
            logger.error(f"Settings update error: {e}")
    
    return render_template('admin_settings.html', config=CONFIG)

# Calendar API endpoints for spreadsheet view
@main_bp.route('/api/test_session')
def test_session():
    """Test endpoint to check session status"""
    user = current_user()
    return jsonify({
        'authenticated': bool(user),
        'username': getattr(user, 'username', None) if user else None,
        'user_id': getattr(user, 'id', None) if user else None,
        'last_seen': session.get('last_seen'),
        'issued_at': session.get('issued_at')
    })

@main_bp.route('/api/test_calendar_data')
def test_calendar_data():
    """Test endpoint for calendar data without authentication"""
    from flask import current_app
    from .services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining, get_risk_level
    from datetime import date, timedelta
    from .models import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get date range from query params
        start_date = request.args.get('start', '')
        end_date = request.args.get('end', '')
        
        # Default to past 180 days + future 8 weeks if no dates provided
        today = date.today()
        if not start_date:
            start_date = (today - timedelta(days=180)).isoformat()
        if not end_date:
            end_date = (today + timedelta(days=56)).isoformat()
        
        # Fetch all employees
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]
        
        # Fetch trips in date range
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.entry_date <= ? AND t.exit_date >= ?
            ORDER BY t.entry_date
        ''', (end_date, start_date))
        
        trips = [dict(row) for row in c.fetchall()]

        # Handle empty database gracefully
        if not employees:
            return jsonify({'resources': [], 'events': []})
        
        # Use fixed compliance start date (October 12, 2025)
        from .services.rolling90 import COMPLIANCE_START_DATE
        compliance_start_date = COMPLIANCE_START_DATE
        
        # Calculate compliance for each employee
        resources = []
        for emp in employees:
            # Get all trips for this employee (not just in date range)
            c.execute('''
                SELECT entry_date, exit_date, country, is_private
                FROM trips 
                WHERE employee_id = ? 
                ORDER BY entry_date
            ''', (emp['id'],))
            emp_trips = [dict(row) for row in c.fetchall()]
            
            # Calculate compliance
            presence = presence_days(emp_trips, compliance_start_date)
            days_used = days_used_in_window(presence, today, compliance_start_date)
            days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)
            
            # Determine risk level and color
            risk_thresholds = {'yellow': 80, 'red': 90}
            risk_level = get_risk_level(days_remaining, risk_thresholds)
            
            if risk_level == 'red':
                color = '#ef4444'  # Red
            elif risk_level == 'yellow':
                color = '#f59e0b'  # Yellow
            else:
                color = '#10b981'  # Green
            
            resources.append({
                'id': emp['id'],
                'title': emp['name'],
                'daysUsed': days_used,
                'daysRemaining': days_remaining,
                'riskLevel': risk_level,
                'color': color
            })
        
        # Format trips as FullCalendar events
        events = []
        for trip in trips:
            # Determine trip color based on employee compliance
            emp_resource = next((r for r in resources if r['id'] == trip['employee_id']), None)
            trip_color = emp_resource['color'] if emp_resource else '#6b7280'
            
            # Format country display
            if trip['is_private']:
                country_display = 'Personal Trip'
            else:
                country_display = f"🇪🇺 {trip['country']}"
            
            events.append({
                'id': trip['id'],
                'resourceId': trip['employee_id'],
                'start': trip['entry_date'],
                'end': (date.fromisoformat(trip['exit_date']) + timedelta(days=1)).isoformat(),  # FullCalendar end is exclusive
                'title': country_display,
                'color': trip_color,
                'extendedProps': {
                    'country': trip['country'],
                    'isPrivate': bool(trip['is_private']),
                    'employeeName': trip['employee_name'],
                    'tooltip': f"{trip['employee_name']}: {country_display} ({trip['entry_date']} - {trip['exit_date']})"
                }
            })
        
        return jsonify({
            'resources': resources,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"Test calendar data API error: {e}")
        return jsonify({'error': str(e)}), 500
    # Connection managed by Flask teardown handler - no need to close

@main_bp.route('/api/calendar_data')
@login_required
def api_calendar_data():
    """Return employees as resources and trips as events for FullCalendar resourceTimeline view"""
    from flask import current_app
    from .services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining, get_risk_level
    from datetime import date, timedelta
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get date range from query params
        start_date = request.args.get('start', '')
        end_date = request.args.get('end', '')
        employee_filter = request.args.get('employee_id', '')
        
        # Default to past 180 days + future 8 weeks if no dates provided
        today = date.today()
        if not start_date:
            start_date = (today - timedelta(days=180)).isoformat()
        if not end_date:
            end_date = (today + timedelta(days=56)).isoformat()
        
        # Fetch all employees
        if employee_filter:
            c.execute('SELECT id, name FROM employees WHERE id = ? ORDER BY name', (employee_filter,))
        else:
            c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]
        
        # Fetch trips in date range
        if employee_filter:
            c.execute('''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                WHERE t.employee_id = ? 
                AND t.entry_date <= ? AND t.exit_date >= ?
                ORDER BY t.entry_date
            ''', (employee_filter, end_date, start_date))
        else:
            c.execute('''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                WHERE t.entry_date <= ? AND t.exit_date >= ?
                ORDER BY t.entry_date
            ''', (end_date, start_date))
        
        trips = [dict(row) for row in c.fetchall()]

        # Handle empty database gracefully
        if not employees:
            return jsonify({'resources': [], 'events': []})
        
        # Use fixed compliance start date (October 12, 2025)
        from .services.rolling90 import COMPLIANCE_START_DATE
        compliance_start_date = COMPLIANCE_START_DATE
        
        # Calculate compliance for each employee
        resources = []
        for emp in employees:
            # Get all trips for this employee (not just in date range)
            c.execute('''
                SELECT entry_date, exit_date, country, is_private
                FROM trips 
                WHERE employee_id = ? 
                ORDER BY entry_date
            ''', (emp['id'],))
            emp_trips = [dict(row) for row in c.fetchall()]
            
            # Calculate compliance
            presence = presence_days(emp_trips, compliance_start_date)
            days_used = days_used_in_window(presence, today, compliance_start_date)
            days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)
            
            # Determine risk level and color
            risk_thresholds = {'yellow': 80, 'red': 90}
            risk_level = get_risk_level(days_remaining, risk_thresholds)
            
            if risk_level == 'red':
                color = '#ef4444'  # Red
            elif risk_level == 'yellow':
                color = '#f59e0b'  # Yellow
            else:
                color = '#10b981'  # Green
            
            resources.append({
                'id': emp['id'],
                'title': emp['name'],
                'daysUsed': days_used,
                'daysRemaining': days_remaining,
                'riskLevel': risk_level,
                'color': color
            })
        
        # Format trips as FullCalendar events
        events = []
        for trip in trips:
            # Determine trip color based on employee compliance
            emp_resource = next((r for r in resources if r['id'] == trip['employee_id']), None)
            trip_color = emp_resource['color'] if emp_resource else '#6b7280'
            
            # Format country display
            if trip['is_private']:
                country_display = 'Personal Trip'
            else:
                country_display = f"🇪🇺 {trip['country']}"
            
            events.append({
                'id': trip['id'],
                'resourceId': trip['employee_id'],
                'start': trip['entry_date'],
                'end': (date.fromisoformat(trip['exit_date']) + timedelta(days=1)).isoformat(),  # FullCalendar end is exclusive
                'title': country_display,
                'color': trip_color,
                'extendedProps': {
                    'country': trip['country'],
                    'isPrivate': bool(trip['is_private']),
                    'employeeName': trip['employee_name'],
                    'tooltip': f"{trip['employee_name']}: {country_display} ({trip['entry_date']} - {trip['exit_date']})"
                }
            })
        
        return jsonify({
            'resources': resources,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"Calendar data API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@main_bp.route('/global_calendar')
@login_required
def global_calendar():
    """Display the global spreadsheet-style calendar view"""
    from flask import current_app
    from datetime import date, timedelta

    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Get all employees for the filter dropdown
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]

        # FIXED: Add missing window_start and window_end variables for template
        today = date.today()
        window_start = today - timedelta(days=179)  # 180-day rolling window
        window_end = today

        return render_template('global_calendar.html',
                            employees=employees,
                            today=today,
                            window_start=window_start,
                            window_end=window_end)
    except Exception as e:
        logger.error(f"Global calendar error: {e}")
        # FIXED: Include window variables in error case too
        today = date.today()
        window_start = today - timedelta(days=179)
        window_end = today

        return render_template('global_calendar.html',
                            employees=[],
                            today=today,
                            window_start=window_start,
                            window_end=window_end)
    finally:
        conn.close()

@main_bp.route('/api/trip_details/<int:trip_id>')
@login_required
def api_trip_details(trip_id):
    """Return detailed trip information for modal display"""
    from flask import current_app
    from .services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining, get_risk_level
    from datetime import date, timedelta
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get trip details
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.id = ?
        ''', (trip_id,))
        
        trip = c.fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
        
        trip_dict = dict(trip)
        
        # Calculate compliance impact
        c.execute('''
            SELECT entry_date, exit_date, country, is_private
            FROM trips 
            WHERE employee_id = ? 
            ORDER BY entry_date
        ''', (trip_dict['employee_id'],))
        emp_trips = [dict(row) for row in c.fetchall()]
        
        presence = presence_days(emp_trips)
        today = date.today()
        days_used = days_used_in_window(presence, today)
        days_remaining = calculate_days_remaining(presence, today)
        
        risk_thresholds = {'yellow': 80, 'red': 90}
        risk_level = get_risk_level(days_remaining, risk_thresholds)
        
        # Calculate trip duration
        entry_date = date.fromisoformat(trip_dict['entry_date'])
        exit_date = date.fromisoformat(trip_dict['exit_date'])
        duration = (exit_date - entry_date).days + 1
        
        return jsonify({
            'trip': trip_dict,
            'compliance': {
                'daysUsed': days_used,
                'daysRemaining': days_remaining,
                'riskLevel': risk_level
            },
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Trip details API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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
            audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
            write_audit(audit_log_path, 'delete_all_data', 'admin', {
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
            audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
            write_audit(audit_log_path, 'delete_all_data_error', 'admin', {'error': str(e)})
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
@main_bp.errorhandler(403)
def forbidden_error(error):
    logger.warning(f"403 error: {error}")
    return render_template('403.html'), 403

@main_bp.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {error}")
    return render_template('404.html'), 404

# ===== REACT FRONTEND API ENDPOINTS =====

@main_bp.route('/api/trips', methods=['GET'])
@login_required
def api_trips_get():
    """Get all trips and employees for React frontend"""
    from flask import current_app
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get all employees
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [dict(row) for row in c.fetchall()]
        
        # Get all trips
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, 
                   t.is_private, t.job_ref, t.ghosted, t.travel_days, t.purpose,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            ORDER BY t.entry_date
        ''')
        trips = [dict(row) for row in c.fetchall()]
        
        return jsonify({
            'employees': employees,
            'trips': trips,
            'generated_at': datetime.now().isoformat()
        })
    finally:
        conn.close()

@main_bp.route('/api/trips', methods=['POST'])
@login_required
def api_trips_post():
    """Create a new trip"""
    from flask import current_app, request
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'country', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Insert new trip
        c.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, 
                             is_private, job_ref, ghosted, travel_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['employee_id'],
            data['country'],
            data['start_date'],
            data['end_date'],
            data.get('is_private', False),
            data.get('job_ref', ''),
            data.get('ghosted', False),
            data.get('travel_days', 0)
        ))
        
        trip_id = c.lastrowid
        conn.commit()
        
        # Return the created trip
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, 
                   t.is_private, t.job_ref, t.ghosted, t.travel_days,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.id = ?
        ''', (trip_id,))
        
        trip = dict(c.fetchone())
        return jsonify(trip), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@main_bp.route('/api/trips/<int:trip_id>', methods=['PATCH'])
@login_required
def api_trips_patch(trip_id):
    """Update an existing trip"""
    from flask import current_app, request
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        data = request.get_json()
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        allowed_fields = ['employee_id', 'country', 'start_date', 'end_date', 
                         'is_private', 'job_ref', 'ghosted', 'travel_days']
        
        for field in allowed_fields:
            if field in data:
                if field in ['start_date', 'end_date']:
                    # Map React field names to database field names
                    db_field = 'entry_date' if field == 'start_date' else 'exit_date'
                    update_fields.append(f'{db_field} = ?')
                    update_values.append(data[field])
                else:
                    update_fields.append(f'{field} = ?')
                    update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_values.append(trip_id)
        
        c.execute(f'''
            UPDATE trips 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        if c.rowcount == 0:
            return jsonify({'error': 'Trip not found'}), 404
        
        conn.commit()
        
        # Return the updated trip
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, 
                   t.is_private, t.job_ref, t.ghosted, t.travel_days,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.id = ?
        ''', (trip_id,))
        
        trip = dict(c.fetchone())
        return jsonify(trip)
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@main_bp.route('/api/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def api_trips_delete(trip_id):
    """Delete a trip"""
    from flask import current_app
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        
        if c.rowcount == 0:
            return jsonify({'error': 'Trip not found'}), 404
        
        conn.commit()
        return jsonify({'id': trip_id})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@main_bp.route('/api/trips/<int:trip_id>/duplicate', methods=['POST'])
@login_required
def api_trips_duplicate(trip_id):
    """Duplicate an existing trip"""
    from flask import current_app, request
    
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        data = request.get_json() or {}
        
        # Get the original trip
        c.execute('''
            SELECT employee_id, country, entry_date, exit_date, 
                   is_private, job_ref, ghosted, travel_days
            FROM trips WHERE id = ?
        ''', (trip_id,))
        
        original = c.fetchone()
        if not original:
            return jsonify({'error': 'Trip not found'}), 404
        
        # Create new trip with overrides
        new_trip = dict(original)
        for key, value in data.items():
            if key in new_trip:
                new_trip[key] = value
        
        c.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, 
                             is_private, job_ref, ghosted, travel_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_trip['employee_id'],
            new_trip['country'],
            new_trip['entry_date'],
            new_trip['exit_date'],
            new_trip['is_private'],
            new_trip['job_ref'],
            new_trip['ghosted'],
            new_trip['travel_days']
        ))
        
        new_trip_id = c.lastrowid
        conn.commit()
        
        # Return the new trip
        c.execute('''
            SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, 
                   t.is_private, t.job_ref, t.ghosted, t.travel_days,
                   e.name as employee_name
            FROM trips t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.id = ?
        ''', (new_trip_id,))
        
        trip = dict(c.fetchone())
        return jsonify(trip), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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
