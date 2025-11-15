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
