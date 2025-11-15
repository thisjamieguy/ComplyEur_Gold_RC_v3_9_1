"""Trip management and planning routes for ComplyEur."""

from __future__ import annotations

import os
import sqlite3
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import flash, jsonify, make_response, render_template, request

from app.middleware.auth import login_required
from .base import (
    main_bp,
    get_db,
    write_audit,
    build_runtime_state,
    allowed_file,
    secure_filename,
    logger,
    validate_trip,
    get_all_future_jobs_for_employee,
    calculate_what_if_scenario,
    export_trips_csv,
)


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
            from app.utils.cache_invalidation import invalidate_dashboard_cache
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
            from app.utils.cache_invalidation import invalidate_dashboard_cache
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
    from app.services.rolling90 import COMPLIANCE_START_DATE
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

@main_bp.route('/api/trip_details/<int:trip_id>')
@login_required
def api_trip_details(trip_id):
    """Return detailed trip information for modal display"""
    from flask import current_app
    from app.services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining, get_risk_level
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
