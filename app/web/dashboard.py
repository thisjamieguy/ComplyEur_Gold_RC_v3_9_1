"""Dashboard and employee overview routes."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, render_template, request, url_for

from app.middleware.auth import login_required
from .base import (
    main_bp,
    logger,
    get_db,
    redact_private_trip_data,
    presence_days,
    days_used_in_window,
    calculate_days_remaining,
    get_risk_level,
    earliest_safe_entry,
    days_until_compliant,
)


@main_bp.route('/home')
@login_required
def home():
    """Home page with quick info and EU travel news"""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']

    import os
    if os.getenv('NEWS_FETCH_ENABLED', 'true').lower() == 'true':
        try:
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

    admin_name = 'Admin'
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT full_name FROM admin WHERE id = 1')
        row = c.fetchone()
        if row and row[0]:
            admin_name = row[0].split()[0] if row[0] else 'Admin'
        conn.close()
    except Exception:
        pass

    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM employees')
    total_employees = c.fetchone()[0]

    from datetime import date
    this_month = date.today().replace(day=1).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM trips WHERE entry_date >= ?', (this_month,))
    trips_this_month = c.fetchone()[0]

    today = date.today()
    at_risk_count = 0
    try:
        c.execute('''
            SELECT COUNT(DISTINCT e.id)
            FROM employees e
            JOIN trips t ON e.id = t.employee_id
            WHERE t.entry_date >= date('now', '-90 days')
            GROUP BY e.id
            HAVING COUNT(t.id) > 0
        ''')
        at_risk_employees = c.fetchall()
        at_risk_count = len(at_risk_employees)
    except Exception:
        pass

    conn.close()

    return render_template(
        'home.html',
        admin_name=admin_name,
        total_employees=total_employees,
        trips_this_month=trips_this_month,
        at_risk_count=at_risk_count,
        config=CONFIG,
    )


@main_bp.route('/dashboard')
@login_required
def dashboard():
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    cache = current_app.config.get('CACHE')
    sort_by = request.args.get('sort_by', 'first_name')
    risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {'green': 30, 'amber': 10})
    cache_key = f"dashboard:{sort_by}"

    if cache:
        try:
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug("Dashboard served from cache")
                return cached_response
        except Exception as e:
            logger.warning(f"Dashboard cache get failed: {e}")

    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = c.fetchall()

        employee_data = []
        at_risk_employees = []
        future_alerts_green = future_alerts_yellow = future_alerts_red = 0

        for employee in employees:
            employee_id, employee_name = employee
            c.execute('''
                SELECT id, country, entry_date, exit_date, purpose, job_ref, ghosted
                FROM trips
                WHERE employee_id = ?
                ORDER BY entry_date DESC
            ''', (employee_id,))
            trips = c.fetchall()
            trips_list = []
            simple_trips = []
            from datetime import date as _date
            today = _date.today()
            for trip in trips:
                trip_id, country, entry_date, exit_date, purpose, job_ref, ghosted = trip
                duration = (datetime.strptime(exit_date, '%Y-%m-%d') - datetime.strptime(entry_date, '%Y-%m-%d')).days + 1
                trip_dict = {
                    'id': trip_id,
                    'country': country,
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'duration': duration,
                    'purpose': purpose,
                    'job_ref': job_ref,
                    'ghosted': ghosted,
                }
                trips_list.append(redact_private_trip_data(trip_dict))
                simple_trips.append({'entry_date': entry_date, 'exit_date': exit_date, 'country': country})

            presence = presence_days(simple_trips, today)
            days_used = days_used_in_window(presence, today)
            days_remaining = calculate_days_remaining(presence, today)
            risk_level = get_risk_level(days_remaining, risk_thresholds)
            earliest_entry = earliest_safe_entry(presence, today)

            employee_data.append({
                'employee_id': employee_id,
                'name': employee_name,
                'trips': trips_list,
                'days_used': days_used,
                'days_remaining': days_remaining,
                'risk_level': risk_level,
                'earliest_safe_entry': earliest_entry
            })

            if days_remaining < risk_thresholds.get('amber', 10):
                at_risk_employees.append(employee_data[-1])

            if days_remaining < 0:
                future_alerts_red += 1
            elif days_remaining < risk_thresholds.get('amber', 10):
                future_alerts_yellow += 1
            else:
                future_alerts_green += 1

        if sort_by == 'risk_level':
            employee_data.sort(key=lambda x: (x['risk_level'], x['days_remaining']))
        else:
            employee_data.sort(key=lambda x: x['name'])

        response = render_template(
            'dashboard.html',
            employees=employee_data,
            at_risk_employees=at_risk_employees,
            future_alerts_summary={
                'red': future_alerts_red,
                'yellow': future_alerts_yellow,
                'green': future_alerts_green,
            },
            sort_by=sort_by,
            risk_thresholds=risk_thresholds,
        )

        if cache:
            try:
                cache.set(cache_key, response, timeout=60)
            except Exception as e:
                logger.warning(f"Failed to cache dashboard response: {e}")

        return response
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading the dashboard. Please try again.', 'error')
        return render_template(
            'dashboard.html',
            employees=[],
            at_risk_employees=[],
            future_alerts_summary={'red': 0, 'yellow': 0, 'green': 0},
            sort_by='first_name',
            risk_thresholds={'green': 30, 'amber': 10},
        )


@main_bp.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    risk_thresholds = CONFIG.get('RISK_THRESHOLDS', {'green': 30, 'amber': 10})

    from .services.rolling90 import COMPLIANCE_START_DATE
    compliance_start_date = COMPLIANCE_START_DATE

    try:
        conn = get_db()
        c = conn.cursor()

        try:
            c.execute('SELECT id, name, created_at FROM employees WHERE id = ?', (employee_id,))
        except sqlite3.OperationalError:
            c.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        employee = c.fetchone()
        if not employee:
            return "Employee not found", 404

        c.execute('SELECT id, employee_id, entry_date, exit_date, country, purpose, job_ref, ghosted, travel_days, is_private FROM trips WHERE employee_id = ? ORDER BY entry_date ASC', (employee_id,))
        rows = c.fetchall()
        logger.debug(f"Employee {employee_id}: Found {len(rows)} trips in database")

        from datetime import date as _date
        today = _date.today()
        trips_list = []
        simple_trips = []
        trip_date_meta = {}
        for row in rows:
            entry_str = row['entry_date']
            exit_str = row['exit_date']
            try:
                entry_dt = _date.fromisoformat(entry_str) if isinstance(entry_str, str) else entry_str
                exit_dt = _date.fromisoformat(exit_str) if isinstance(exit_str, str) else exit_str
            except Exception:
                entry_dt, exit_dt = today, today
            duration = (exit_dt - entry_dt).days + 1
            trip_date_meta[row['id']] = {'entry': entry_dt, 'exit': exit_dt}
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
                'is_private': (row['is_private'] if 'is_private' in row.keys() else False),
            }
            trips_list.append(redact_private_trip_data(trip_dict))
            simple_trips.append({'entry_date': entry_str, 'exit_date': exit_str, 'country': row['country']})

        presence = presence_days(simple_trips, today)
        days_used = days_used_in_window(presence, today, compliance_start_date)
        days_remaining = calculate_days_remaining(presence, today, compliance_start_date=compliance_start_date)
        risk_level = get_risk_level(days_remaining, risk_thresholds)
        safe_entry = earliest_safe_entry(presence, today, compliance_start_date=compliance_start_date)
        days_until_safe = None
        compliant_date = None
        if days_remaining < 0:
            days_until_safe, compliant_date = days_until_compliant(presence, today, compliance_start_date=compliance_start_date)

        limit = 90
        trip_metrics = {}
        for trip_id, meta in trip_date_meta.items():
            baseline = meta.get('exit') or meta.get('entry') or today
            ref_point = baseline + timedelta(days=1)
            remaining_after_trip = calculate_days_remaining(presence, ref_point, compliance_start_date=compliance_start_date)
            trip_metrics[trip_id] = {
                'days_remaining_after': remaining_after_trip,
                'days_used_to_date': limit - remaining_after_trip,
                'risk_level_after': get_risk_level(remaining_after_trip, risk_thresholds),
            }

        for trip in trips_list:
            metrics = trip_metrics.get(trip['id'])
            if metrics:
                trip['days_remaining_after'] = metrics['days_remaining_after']
                trip['risk_level_after'] = metrics['risk_level_after']
                trip['days_used_to_date'] = metrics['days_used_to_date']
            else:
                trip['days_remaining_after'] = days_remaining
                trip['risk_level_after'] = risk_level
                trip['days_used_to_date'] = days_used

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
