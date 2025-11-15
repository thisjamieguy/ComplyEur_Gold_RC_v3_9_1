"""Reporting orchestration helpers."""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any, Dict, List

from app.repositories import reports_repository
from .compliance_forecast import get_all_future_jobs_for_employee


FUTURE_ALERT_HEADERS = [
    'Employee',
    'Risk Level',
    'Job Start',
    'Job End',
    'Country',
    'Job Duration (days)',
    'Days Used Before',
    'Days After Job',
    'Days Remaining',
    'Compliant From',
]


def _format_date(value) -> str:
    if not value:
        return ''
    if isinstance(value, date):
        return value.strftime('%d-%m-%Y')
    return value


def build_future_alert_rows(
    db_path: str,
    warning_threshold: int,
    compliance_start_date: date,
) -> List[Dict[str, Any]]:
    """Return rows ready for CSV export for future job alerts."""
    employees = reports_repository.fetch_employees_with_trips(db_path)
    rows: List[Dict[str, Any]] = []
    for emp in employees:
        trips = emp.get('trips', [])
        forecasts = get_all_future_jobs_for_employee(
            emp['id'],
            trips,
            warning_threshold,
            compliance_start_date,
        )
        for forecast in forecasts:
            rows.append({
                'Employee': emp['name'],
                'Risk Level': forecast['risk_level'],
                'Job Start': _format_date(forecast['job_start_date']),
                'Job End': _format_date(forecast['job_end_date']),
                'Country': (forecast['job'].get('country') or forecast['job'].get('country_code', '')),
                'Job Duration (days)': forecast['job_duration'],
                'Days Used Before': forecast['days_used_before_job'],
                'Days After Job': forecast['days_after_job'],
                'Days Remaining': forecast['days_remaining_after_job'],
                'Compliant From': _format_date(forecast.get('compliant_from_date')),
            })
    return rows


def generate_future_alerts_csv(
    db_path: str,
    warning_threshold: int,
    compliance_start_date: date,
) -> str:
    """Generate CSV identical to the legacy /export_future_alerts output."""
    rows = build_future_alert_rows(db_path, warning_threshold, compliance_start_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(FUTURE_ALERT_HEADERS)
    for row in rows:
        writer.writerow([row[header] for header in FUTURE_ALERT_HEADERS])
    return output.getvalue()
