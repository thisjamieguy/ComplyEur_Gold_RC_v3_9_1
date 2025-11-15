"""What-if scenario service helpers."""

from __future__ import annotations

from datetime import date as date_cls
from typing import Any, Dict, List

from app.repositories import scenario_repository
from .compliance_forecast import calculate_what_if_scenario


def list_employees(db_path: str) -> List[Dict[str, Any]]:
    """Return employee id/name pairs for the scenario UI."""
    return scenario_repository.fetch_employees(db_path)


def calculate_scenario(
    db_path: str,
    employee_id: int,
    start_iso: str,
    end_iso: str,
    country: str,
    warning_threshold: int,
) -> Dict[str, Any]:
    """Calculate the what-if scenario payload."""
    trips = scenario_repository.fetch_employee_trips(db_path, employee_id)
    scenario = calculate_what_if_scenario(
        employee_id,
        trips,
        date_cls.fromisoformat(start_iso),
        date_cls.fromisoformat(end_iso),
        country,
        warning_threshold,
    )
    response = {
        "employee_name": "",
        "job_duration": scenario["job_duration"],
        "days_used_before": scenario["days_used_before_job"],
        "days_after": scenario["days_after_job"],
        "days_remaining": scenario["days_remaining_after_job"],
        "risk_level": scenario["risk_level"],
        "is_schengen": scenario["is_schengen"],
        "compliant_from_date": scenario["compliant_from_date"].isoformat()
        if scenario.get("compliant_from_date")
        else None,
    }
    employee_name = scenario_repository.fetch_employee_name(db_path, employee_id)
    if employee_name:
        response["employee_name"] = employee_name
    return response
