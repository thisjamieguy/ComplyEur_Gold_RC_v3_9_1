"""Privacy, GDPR, and compliance tools."""

from __future__ import annotations

from datetime import datetime

from flask import current_app, flash, jsonify, redirect, render_template, request, send_file, url_for

from app.middleware.auth import login_required
from .base import (
    ATTEMPT_WINDOW_SECONDS,
    LOGIN_ATTEMPTS,
    MAX_ATTEMPTS,
    anonymize_employee,
    create_dsar_export,
    current_actor,
    delete_employee_data,
    get_db,
    get_expired_trips,
    load_config,
    purge_expired_trips,
    rectify_employee_name,
    write_audit,
    main_bp,
)


@main_bp.route('/privacy')
def privacy():
    config = current_app.config['CONFIG']
    return render_template(
        'privacy.html',
        current_date=datetime.now().strftime('%Y-%m-%d'),
        retention_months=config.get('RETENTION_MONTHS', 36),
        session_timeout_minutes=config.get('SESSION_IDLE_TIMEOUT_MINUTES', 30),
        max_login_attempts=MAX_ATTEMPTS,
        rate_limit_window=ATTEMPT_WINDOW_SECONDS // 60,
    )


@main_bp.route('/privacy-policy')
def privacy_policy():
    return redirect(url_for('main.privacy'))


@main_bp.route('/cookie-policy')
def cookie_policy():
    return render_template('cookie_policy.html', current_date=datetime.now().strftime('%Y-%m-%d'))


@main_bp.route('/admin_privacy_tools')
@login_required
def admin_privacy_tools():
    config = current_app.config['CONFIG']
    retention_months = config.get('RETENTION_MONTHS', 36)
    db_path = current_app.config['DATABASE']
    try:
        trips = get_expired_trips(db_path, retention_months)
        expired_count = len(trips)
    except Exception:
        expired_count = 0
    return render_template(
        'admin_privacy_tools.html',
        retention_months=retention_months,
        expired_count=expired_count,
        last_purge=None,
    )


@main_bp.route('/admin/privacy-tools')
@login_required
def admin_privacy_tools_alias():
    return render_template('admin_privacy_tools.html')


@main_bp.route('/api/retention/preview')
@login_required
def retention_preview():
    retention_months = current_app.config['CONFIG'].get('RETENTION_MONTHS', 36)
    db_path = current_app.config['DATABASE']
    try:
        trips = get_expired_trips(db_path, retention_months)
        employees_affected = len({t['employee_id'] for t in trips})
        return jsonify({'success': True, 'trips_count': len(trips), 'employees_affected': employees_affected})
    except Exception as exc:
        current_app.logger.error("Retention preview error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/admin/retention/expired')
@login_required
def retention_expired():
    retention_months = current_app.config['CONFIG'].get('RETENTION_MONTHS', 36)
    db_path = current_app.config['DATABASE']
    try:
        trips = get_expired_trips(db_path, retention_months)
    except Exception:
        trips = []
    return render_template('expired_trips.html', trips=trips, retention_months=retention_months)


@main_bp.route('/admin/retention/purge', methods=['POST'])
@login_required
def retention_purge():
    config = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    retention_months = config.get('RETENTION_MONTHS', 36)
    try:
        result = purge_expired_trips(db_path, retention_months)
        write_audit(config['AUDIT_LOG_PATH'], 'retention_purge', current_actor(), result)
        flash(f"Purged {result.get('trips_deleted', 0)} expired trip entries.", 'success')
        return jsonify({'success': True, **result})
    except Exception as exc:
        current_app.logger.error("Retention purge error: %s", exc)
        write_audit(config['AUDIT_LOG_PATH'], 'retention_purge_error', current_actor(), {'error': str(exc)})
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/admin/dsar/export/<int:employee_id>')
@login_required
def dsar_export(employee_id: int):
    config = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = create_dsar_export(db_path, employee_id, config['DSAR_EXPORT_DIR'], config.get('RETENTION_MONTHS', 36))
        if not result.get('success'):
            return jsonify(result), 404
        write_audit(config['AUDIT_LOG_PATH'], 'dsar_export', current_actor(), {'employee_id': employee_id, 'file': result['filename']})
        return send_file(result['file_path'], as_attachment=True, download_name=result['filename'])
    except Exception as exc:
        current_app.logger.error("DSAR export error: %s", exc)
        write_audit(config['AUDIT_LOG_PATH'], 'dsar_export_error', current_actor(), {'employee_id': employee_id, 'error': str(exc)})
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/admin/dsar/rectify/<int:employee_id>', methods=['POST'])
@login_required
def dsar_rectify(employee_id: int):
    config = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        payload = request.get_json(force=True) or {}
        new_name = (payload.get('new_name') or '').strip()
        result = rectify_employee_name(db_path, employee_id, new_name)
        event = 'dsar_rectify' if result.get('success') else 'dsar_rectify_failed'
        write_audit(config['AUDIT_LOG_PATH'], event, current_actor(), {'employee_id': employee_id, 'new_name': new_name, 'error': result.get('error')})
        return jsonify(result)
    except Exception as exc:
        current_app.logger.error("DSAR rectify error: %s", exc)
        write_audit(config['AUDIT_LOG_PATH'], 'dsar_rectify_error', current_actor(), {'employee_id': employee_id, 'error': str(exc)})
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/admin/dsar/delete/<int:employee_id>', methods=['POST'])
@login_required
def dsar_delete(employee_id: int):
    config = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = delete_employee_data(db_path, employee_id)
        event = 'dsar_delete' if result.get('success') else 'dsar_delete_failed'
        write_audit(config['AUDIT_LOG_PATH'], event, current_actor(), {'employee_id': employee_id, 'trips_deleted': result.get('trips_deleted'), 'error': result.get('error')})
        return jsonify(result)
    except Exception as exc:
        current_app.logger.error("DSAR delete error: %s", exc)
        write_audit(config['AUDIT_LOG_PATH'], 'dsar_delete_error', current_actor(), {'employee_id': employee_id, 'error': str(exc)})
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/admin/dsar/anonymize/<int:employee_id>', methods=['POST'])
@login_required
def dsar_anonymize(employee_id: int):
    config = current_app.config['CONFIG']
    db_path = current_app.config['DATABASE']
    try:
        result = anonymize_employee(db_path, employee_id)
        event = 'dsar_anonymize' if result.get('success') else 'dsar_anonymize_failed'
        write_audit(config['AUDIT_LOG_PATH'], event, current_actor(), {'employee_id': employee_id, 'new_name': result.get('new_name'), 'error': result.get('error')})
        return jsonify(result)
    except Exception as exc:
        current_app.logger.error("DSAR anonymize error: %s", exc)
        write_audit(config['AUDIT_LOG_PATH'], 'dsar_anonymize_error', current_actor(), {'employee_id': employee_id, 'error': str(exc)})
        return jsonify({'success': False, 'error': str(exc)}), 500
