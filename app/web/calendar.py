"""Calendar-related routes for ComplyEur."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta

from flask import current_app, jsonify, redirect, render_template, request, url_for

from app.middleware.auth import login_required
from .base import main_bp, get_db, logger


def _is_calendar_enabled():
    """Check if calendar feature should be accessible (dev mode only)."""
    config = current_app.config.get('CONFIG', {})
    if config.get('CALENDAR_DEV_MODE', False):
        return True

    if os.getenv('CALENDAR_DEV_MODE', '').lower() in ('true', '1', 'yes'):
        return True

    is_production = (
        os.getenv('FLASK_ENV') == 'production'
        or os.getenv('RENDER') == 'true'
        or os.getenv('RENDER_EXTERNAL_HOSTNAME')
    )
    return not is_production  # Available in non-production environments


@main_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view - only accessible in development mode."""
    if not _is_calendar_enabled():
        return (
            '<html><body><h1>Calendar Unavailable</h1><p>This feature is currently in development and not '
            'available in production.</p><p>For development access, set CALENDAR_DEV_MODE=true in your '
            'environment or config.</p></body></html>',
            403,
        )

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

    return render_template(
        'calendar.html',
        employee_id=employee_id,
        employee_name=employee_name,
        config={'CONFIG': config},
    )


@main_bp.route('/calendar_dev')
@login_required
def calendar_dev():
    """Development-only calendar access route."""
    if not _is_calendar_enabled():
        return (
            '<html><body><h1>Development Access Only</h1><p>This route is only available in development mode.</p></body></html>',
            403,
        )
    return redirect(url_for('main.calendar'))


@main_bp.route('/calendar_view')
@login_required
def calendar_view():
    """Redirect to calendar (if enabled)."""
    if not _is_calendar_enabled():
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.calendar'))


@main_bp.route('/api/test_calendar_data')
def test_calendar_data():
    """Test endpoint for calendar data without authentication."""
    from app.services.rolling90 import (
        COMPLIANCE_START_DATE,
        calculate_days_remaining,
        days_used_in_window,
        get_risk_level,
        presence_days,
    )

    conn = get_db()
    c = conn.cursor()

    try:
        start_date = request.args.get('start', '')
        end_date = request.args.get('end', '')

        today = date.today()
        if not start_date:
            start_date = (today - timedelta(days=180)).isoformat()
        if not end_date:
            end_date = (today + timedelta(days=56)).isoformat()

        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]

        c.execute(
            '''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                WHERE t.entry_date <= ? AND t.exit_date >= ?
                ORDER BY t.entry_date
            ''',
            (end_date, start_date),
        )

        trips = [dict(row) for row in c.fetchall()]

        if not employees:
            return jsonify({'resources': [], 'events': []})

        compliance_start_date = COMPLIANCE_START_DATE

        resources = []
        for emp in employees:
            c.execute(
                '''
                    SELECT entry_date, exit_date, country, is_private
                    FROM trips
                    WHERE employee_id = ?
                    ORDER BY entry_date
                ''',
                (emp['id'],),
            )
            emp_trips = [dict(row) for row in c.fetchall()]

            presence = presence_days(emp_trips, compliance_start_date)
            days_used = days_used_in_window(presence, today, compliance_start_date)
            days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)

            risk_thresholds = {'yellow': 80, 'red': 90}
            risk_level = get_risk_level(days_remaining, risk_thresholds)

            if risk_level == 'red':
                color = '#ef4444'
            elif risk_level == 'yellow':
                color = '#f59e0b'
            else:
                color = '#10b981'

            resources.append(
                {
                    'id': emp['id'],
                    'title': emp['name'],
                    'daysUsed': days_used,
                    'daysRemaining': days_remaining,
                    'riskLevel': risk_level,
                    'color': color,
                }
            )

        events = []
        for trip in trips:
            emp_resource = next((r for r in resources if r['id'] == trip['employee_id']), None)
            trip_color = emp_resource['color'] if emp_resource else '#6b7280'

            if trip['is_private']:
                country_display = 'Personal Trip'
            else:
                country_display = f"🇪🇺 {trip['country']}"

            events.append(
                {
                    'id': trip['id'],
                    'resourceId': trip['employee_id'],
                    'start': trip['entry_date'],
                    'end': (date.fromisoformat(trip['exit_date']) + timedelta(days=1)).isoformat(),
                    'title': country_display,
                    'color': trip_color,
                    'extendedProps': {
                        'country': trip['country'],
                        'isPrivate': bool(trip['is_private']),
                        'employeeName': trip['employee_name'],
                        'tooltip': f"{trip['employee_name']}: {country_display} ({trip['entry_date']} - {trip['exit_date']})",
                    },
                }
            )

        return jsonify({'resources': resources, 'events': events})

    except Exception as e:
        logger.error(f"Test calendar data API error: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/calendar_data')
@login_required
def api_calendar_data():
    """Return employees as resources and trips as events for FullCalendar resourceTimeline view."""
    from app.services.rolling90 import (
        COMPLIANCE_START_DATE,
        calculate_days_remaining,
        days_used_in_window,
        get_risk_level,
        presence_days,
    )

    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        start_date = request.args.get('start', '')
        end_date = request.args.get('end', '')
        employee_filter = request.args.get('employee_id', '')

        today = date.today()
        if not start_date:
            start_date = (today - timedelta(days=180)).isoformat()
        if not end_date:
            end_date = (today + timedelta(days=56)).isoformat()

        if employee_filter:
            c.execute('SELECT id, name FROM employees WHERE id = ? ORDER BY name', (employee_filter,))
        else:
            c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]

        if employee_filter:
            c.execute(
                '''
                    SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                           e.name as employee_name
                    FROM trips t
                    JOIN employees e ON t.employee_id = e.id
                    WHERE t.employee_id = ?
                    AND t.entry_date <= ? AND t.exit_date >= ?
                    ORDER BY t.entry_date
                ''',
                (employee_filter, end_date, start_date),
            )
        else:
            c.execute(
                '''
                    SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date, t.is_private,
                           e.name as employee_name
                    FROM trips t
                    JOIN employees e ON t.employee_id = e.id
                    WHERE t.entry_date <= ? AND t.exit_date >= ?
                    ORDER BY t.entry_date
                ''',
                (end_date, start_date),
            )

        trips = [dict(row) for row in c.fetchall()]

        if not employees:
            return jsonify({'resources': [], 'events': []})

        compliance_start_date = COMPLIANCE_START_DATE

        resources = []
        for emp in employees:
            c.execute(
                '''
                    SELECT entry_date, exit_date, country, is_private
                    FROM trips
                    WHERE employee_id = ?
                    ORDER BY entry_date
                ''',
                (emp['id'],),
            )
            emp_trips = [dict(row) for row in c.fetchall()]

            presence = presence_days(emp_trips, compliance_start_date)
            days_used = days_used_in_window(presence, today, compliance_start_date)
            days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)

            risk_thresholds = {'yellow': 80, 'red': 90}
            risk_level = get_risk_level(days_remaining, risk_thresholds)

            if risk_level == 'red':
                color = '#ef4444'
            elif risk_level == 'yellow':
                color = '#f59e0b'
            else:
                color = '#10b981'

            resources.append(
                {
                    'id': emp['id'],
                    'title': emp['name'],
                    'daysUsed': days_used,
                    'daysRemaining': days_remaining,
                    'riskLevel': risk_level,
                    'color': color,
                }
            )

        events = []
        for trip in trips:
            emp_resource = next((r for r in resources if r['id'] == trip['employee_id']), None)
            trip_color = emp_resource['color'] if emp_resource else '#6b7280'

            if trip['is_private']:
                country_display = 'Personal Trip'
            else:
                country_display = f"🇪🇺 {trip['country']}"

            events.append(
                {
                    'id': trip['id'],
                    'resourceId': trip['employee_id'],
                    'start': trip['entry_date'],
                    'end': (date.fromisoformat(trip['exit_date']) + timedelta(days=1)).isoformat(),
                    'title': country_display,
                    'color': trip_color,
                    'extendedProps': {
                        'country': trip['country'],
                        'isPrivate': bool(trip['is_private']),
                        'employeeName': trip['employee_name'],
                        'tooltip': f"{trip['employee_name']}: {country_display} ({trip['entry_date']} - {trip['exit_date']})",
                    },
                }
            )

        return jsonify({'resources': resources, 'events': events})

    except Exception as e:
        logger.error(f"Calendar data API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@main_bp.route('/global_calendar')
@login_required
def global_calendar():
    """Display the global spreadsheet-style calendar view."""
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [{'id': row['id'], 'name': row['name']} for row in c.fetchall()]

        today = date.today()
        window_start = today - timedelta(days=179)
        window_end = today

        return render_template(
            'global_calendar.html',
            employees=employees,
            today=today,
            window_start=window_start,
            window_end=window_end,
        )
    except Exception as e:
        logger.error(f"Global calendar error: {e}")
        today = date.today()
        window_start = today - timedelta(days=179)
        window_end = today
        return render_template(
            'global_calendar.html',
            employees=[],
            today=today,
            window_start=window_start,
            window_end=window_end,
        )
    finally:
        conn.close()
