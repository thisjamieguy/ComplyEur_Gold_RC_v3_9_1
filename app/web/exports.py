"""Exports-related routes for ComplyEur."""

from __future__ import annotations

import csv
import io

from flask import jsonify, make_response

from app.middleware.auth import login_required
from .base import (
    main_bp,
    get_db,
    get_all_future_jobs_for_employee,
    export_trips_csv,
    logger,
)


@main_bp.route('/export_future_alerts')
@login_required
def export_future_alerts():
    """Export future job alerts to CSV."""
    from flask import current_app
    CONFIG = current_app.config['CONFIG']
    warning_threshold = CONFIG.get('FUTURE_JOB_WARNING_THRESHOLD', 80)

    # Use fixed compliance start date (October 12, 2025)
    from app.services.rolling90 import COMPLIANCE_START_DATE

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
