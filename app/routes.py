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
from app.web.base import (
    main_bp,
    logger,
    Hasher,
    write_audit,
    purge_expired_trips,
    get_expired_trips,
    anonymize_employee,
    create_dsar_export,
    delete_employee_data,
    rectify_employee_name,
    export_trips_csv,
    export_employee_report_pdf,
    export_all_employees_report_pdf,
    presence_days,
    days_used_in_window,
    earliest_safe_entry,
    calculate_days_remaining,
    get_risk_level,
    days_until_compliant,
    validate_trip,
    validate_date_range,
    calculate_future_job_compliance,
    get_all_future_jobs_for_employee,
    calculate_what_if_scenario,
    get_risk_level_for_forecast,
    create_backup,
    auto_backup_if_needed,
    list_backups,
    LOGIN_ATTEMPTS,
    MAX_ATTEMPTS,
    ATTEMPT_WINDOW_SECONDS,
    redact_private_trip_data,
    get_db,
    current_actor,
    verify_and_upgrade_password,
    allowed_file,
)
import app.web.pages  # noqa: E402,F401
import app.web.privacy  # noqa: E402,F401

# Load environment variables
load_dotenv()

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
    actor = current_actor()
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
