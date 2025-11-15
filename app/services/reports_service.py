"""Reporting orchestration helpers."""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any, Dict, List, Sequence, Tuple

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
    return str(value)


def get_future_alerts(
    db_path: str,
    warning_threshold: int,
    compliance_start_date: date,
) -> List[Dict[str, Any]]:
    """Collect future job alerts for all employees."""
    employees = reports_repository.fetch_employees_with_trips(db_path)
    forecasts: List[Dict[str, Any]] = []
    for emp in employees:
        trips = emp.get('trips', [])
        future_jobs = get_all_future_jobs_for_employee(
            emp['id'],
            trips,
            warning_threshold,
            compliance_start_date,
        )
        for forecast in future_jobs:
            enriched = dict(forecast)
            enriched['employee_name'] = emp['name']
            forecasts.append(enriched)
    return forecasts


def summarise_future_alerts(forecasts: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Return counts for each risk tier."""
    return {
        'red': sum(1 for f in forecasts if f['risk_level'] == 'red'),
        'yellow': sum(1 for f in forecasts if f['risk_level'] == 'yellow'),
        'green': sum(1 for f in forecasts if f['risk_level'] == 'green'),
    }


def filter_and_sort_future_alerts(
    forecasts: Sequence[Dict[str, Any]],
    risk_filter: str = 'all',
    sort_by: str = 'risk',
) -> List[Dict[str, Any]]:
    """Apply risk filtering and sorting identical to the legacy view."""
    if risk_filter in {'red', 'yellow', 'green'}:
        filtered = [f for f in forecasts if f['risk_level'] == risk_filter]
    else:
        filtered = list(forecasts)

    if sort_by == 'date':
        filtered.sort(key=lambda f: f['job_start_date'])
    elif sort_by == 'employee':
        filtered.sort(key=lambda f: f.get('employee_name', ''))
    elif sort_by == 'days':
        filtered.sort(key=lambda f: f.get('days_after_job', 0), reverse=True)
    else:
        risk_order = {'red': 0, 'yellow': 1, 'green': 2}
        filtered.sort(key=lambda f: risk_order.get(f['risk_level'], 3))
    return filtered


def _forecast_to_row(forecast: Dict[str, Any]) -> List[Any]:
    """Map forecast data to CSV row format."""
    return [
        forecast.get('employee_name', ''),
        forecast['risk_level'],
        _format_date(forecast['job_start_date']),
        _format_date(forecast['job_end_date']),
        (forecast['job'].get('country') or forecast['job'].get('country_code', '')),
        forecast['job_duration'],
        forecast['days_used_before_job'],
        forecast['days_after_job'],
        forecast['days_remaining_after_job'],
        _format_date(forecast.get('compliant_from_date')),
    ]


def generate_future_alerts_csv(
    db_path: str,
    warning_threshold: int,
    compliance_start_date: date,
) -> str:
    """Generate CSV identical to the legacy /export_future_alerts output."""
    forecasts = get_future_alerts(db_path, warning_threshold, compliance_start_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(FUTURE_ALERT_HEADERS)
    for forecast in forecasts:
        writer.writerow(_forecast_to_row(forecast))
    return output.getvalue()
