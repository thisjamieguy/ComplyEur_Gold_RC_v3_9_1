"""Administrative routes for ComplyEur."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.middleware.auth import login_required, current_user
from .base import (
    main_bp,
    Hasher,
    LOGIN_ATTEMPTS,
    MAX_ATTEMPTS,
    ATTEMPT_WINDOW_SECONDS,
    write_audit,
    get_db,
    current_actor,
    logger,
    verify_and_upgrade_password,
)


@main_bp.route('/api/news/refresh', methods=['POST'])
@login_required
def refresh_news():
    """Manually refresh news from all sources."""
    try:
        from app.services.news_fetcher import fetch_news_from_sources

        db_path = current_app.config['DATABASE']

        def refresh_news_bg():
            try:
                news_items = fetch_news_from_sources(db_path)
                logger.info("Background news refresh completed: %d items", len(news_items))
            except Exception as exc:
                logger.error("Background news refresh failed: %s", exc)

        thread = threading.Thread(target=refresh_news_bg)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'News refresh started in background'})
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({'success': False, 'message': f'Error starting news refresh: {exc}'}), 500


# Login route moved to auth_bp - this route disabled to avoid conflicts
# @main_bp.route('/login', methods=['GET', 'POST'])
def login_old():  # pragma: no cover - legacy
    if request.method == 'POST':
        CONFIG = current_app.config['CONFIG']
        ip = request.remote_addr or 'local'
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
    """User registration for new accounts."""
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

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

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM admin WHERE id = 1')
        existing_admin = c.fetchone()

        if existing_admin:
            conn.close()
            return render_template('signup.html', error='An admin account already exists. Please contact support for access.')

        try:
            hasher = Hasher()
            password_hash = hasher.hash(password)

            c.execute(
                '''
                    INSERT INTO admin (id, password_hash, company_name, full_name, email, phone, created_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?)
                ''',
                (password_hash, company_name, full_name, email, phone, datetime.utcnow()),
            )

            conn.commit()
            conn.close()

            CONFIG = current_app.config['CONFIG']
            write_audit(
                CONFIG['AUDIT_LOG_PATH'],
                'admin_signup',
                'system',
                {'company_name': company_name, 'email': email, 'full_name': full_name},
            )

            return render_template('login.html', success='Account created successfully! Please log in with your credentials.')

        except Exception as exc:  # pragma: no cover - defensive
            conn.rollback()
            conn.close()
            logger.error("Signup error: %s", exc)
            return render_template('signup.html', error='An error occurred during registration. Please try again.')

    return render_template('signup.html')


@main_bp.route('/get-started')
def get_started():
    """Alias for signup page."""
    return redirect(url_for('main.signup'))


@main_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """First-time setup to create admin account."""
    from app.models import Admin

    if Admin.exists():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        if password:
            hasher = Hasher()
            password_hash = hasher.hash(password)
            Admin.set_password_hash(password_hash)
            return render_template('login.html', success='Admin account created successfully. Please log in.')
        return render_template('setup.html', error='Password is required')

    return render_template('setup.html')


@main_bp.route('/logout')
def logout():
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
    """Display admin settings and handle form submission."""
    CONFIG = current_app.config['CONFIG']

    if request.method == 'POST':
        try:
            config_updates = {}

            if 'retention_months' in request.form:
                config_updates['RETENTION_MONTHS'] = int(request.form['retention_months'])

            if 'session_timeout' in request.form:
                config_updates['SESSION_IDLE_TIMEOUT_MINUTES'] = int(request.form['session_timeout'])

            config_updates['SESSION_COOKIE_SECURE'] = 'session_cookie_secure' in request.form

            if 'password_scheme' in request.form:
                config_updates['PASSWORD_HASH_SCHEME'] = request.form['password_scheme']

            if 'export_dir' in request.form:
                config_updates['DSAR_EXPORT_DIR'] = request.form['export_dir']

            if 'audit_log' in request.form:
                config_updates['AUDIT_LOG_PATH'] = request.form['audit_log']

            if 'warning_threshold' in request.form:
                config_updates['FUTURE_JOB_WARNING_THRESHOLD'] = int(request.form['warning_threshold'])

            if 'risk_threshold_green' in request.form and 'risk_threshold_amber' in request.form:
                risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {})
                risk_thresholds['green'] = int(request.form['risk_threshold_green'])
                risk_thresholds['amber'] = int(request.form['risk_threshold_amber'])
                config_updates['RISK_THRESHOLDS'] = risk_thresholds

            if 'news_filter_region' in request.form:
                config_updates['NEWS_FILTER_REGION'] = request.form['news_filter_region']

            if config_updates:
                CONFIG.update(config_updates)

                with open('config.py', 'r', encoding='utf-8') as handle:
                    content = handle.read()

                for key, value in config_updates.items():
                    if key == 'RISK_THRESHOLDS':
                        content = re.sub(rf'{key}\s*=\s*{{[^}}]*}}', f'{key} = {value}', content)
                    else:
                        content = re.sub(rf'{key}\s*=\s*[^\n]*', f'{key} = {repr(value)}', content)

                with open('config.py', 'w', encoding='utf-8') as handle:
                    handle.write(content)

                flash('Settings updated successfully!', 'success')
            else:
                flash('No changes were made.', 'info')

        except Exception as exc:  # pragma: no cover - defensive
            flash(f'Error updating settings: {exc}', 'error')
            logger.error("Settings update error: %s", exc)

    return render_template('admin_settings.html', config=CONFIG)


@main_bp.route('/api/test_session')
def test_session():
    """Test endpoint to check session status."""
    user = current_user()
    return jsonify(
        {
            'authenticated': bool(user),
            'username': getattr(user, 'username', None) if user else None,
            'user_id': getattr(user, 'id', None) if user else None,
            'last_seen': session.get('last_seen'),
            'issued_at': session.get('issued_at'),
        }
    )


@main_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change admin password."""
    return redirect(url_for('main.admin_settings'))


@main_bp.route('/delete_all_data', methods=['POST'])
@login_required
def delete_all_data():
    """Delete all data (employees, trips, exported files)."""
    CONFIG = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']

    referrer = request.referrer or ''

    def redirect_back():
        if '/import_excel' in referrer:
            return redirect(url_for('main.import_excel'))
        return redirect(url_for('main.admin_settings'))

    try:
        if 'confirmation' in request.form:
            if request.form.get('confirmation', '').strip() != 'DELETE ALL DATA':
                flash('You must type "DELETE ALL DATA" to confirm this action.')
                return redirect_back()

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

        try:
            c.execute('DELETE FROM trips WHERE is_private = 0 OR is_private IS NULL')
        except Exception:
            pass

        try:
            c.execute(
                '''
                    DELETE FROM employees
                    WHERE id NOT IN (
                        SELECT DISTINCT employee_id FROM trips
                    )
                '''
            )
        except Exception:
            pass
        try:
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        exports_dir = CONFIG.get('DSAR_EXPORT_DIR')
        export_files_deleted = 0
        if exports_dir and os.path.isdir(exports_dir):
            for root, _dirs, files in os.walk(exports_dir):
                for filename in files:
                    try:
                        os.remove(os.path.join(root, filename))
                        export_files_deleted += 1
                    except Exception:
                        pass

        try:
            audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
            write_audit(
                audit_log_path,
                'delete_all_data',
                'admin',
                {
                    'employees_deleted': employees_before,
                    'trips_deleted': trips_before - private_trips_before,
                    'private_trips_preserved': private_trips_before,
                    'export_files_deleted': export_files_deleted,
                },
            )
        except Exception:
            pass

        if private_trips_before > 0:
            flash(
                f'All business travel data cleared successfully. {private_trips_before} personal holiday trip(s) preserved.'
            )
        else:
            flash('All data has been cleared successfully.')
        return redirect_back()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Delete all data error: %s", exc)
        try:
            audit_log_path = CONFIG.get('AUDIT_LOG_PATH', 'logs/audit.log')
            write_audit(audit_log_path, 'delete_all_data_error', 'admin', {'error': str(exc)})
        except Exception:
            pass
        flash(f'Failed to delete data: {exc}')
        return redirect_back()


@main_bp.route('/reset_admin_password', methods=['GET', 'POST'])
def reset_admin_password():
    """Emergency admin password reset - remove this route after use."""
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        if new_password and len(new_password) >= 6:
            from app.models import Admin

            hasher = Hasher()
            password_hash = hasher.hash(new_password)
            Admin.set_password_hash(password_hash)
            return render_template(
                'login.html', success='Admin password reset successfully. Please log in with your new password.'
            )
        return render_template('reset_password.html', error='Password must be at least 6 characters')

    return render_template('reset_password.html')


@main_bp.route('/dev/admin-bootstrap', methods=['GET', 'POST'])
def dev_admin_bootstrap():
    """
    Development-only admin bootstrap route.
    Only available when FLASK_ENV=development and LOCAL_ADMIN_SETUP_TOKEN is set.
    """
    if current_app.config.get('ENV') != 'development' and os.getenv('FLASK_ENV') != 'development':
        return "Not available in production", 403

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

        from app.models import Admin

        hasher = Hasher()
        password_hash = hasher.hash(new_password)
        Admin.set_password_hash(password_hash)

        return render_template('login.html', success='Admin account created successfully. Please log in.')

    return render_template('setup.html', dev_mode=True)
