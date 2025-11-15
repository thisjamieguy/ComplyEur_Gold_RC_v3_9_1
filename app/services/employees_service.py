"""Employees domain service layer."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from app.repositories import employees_repository


class EmployeeValidationError(ValueError):
    """Raised when employee input fails validation."""


def _validate_employee_name(raw_name: Any) -> str:
    """Normalize and validate employee names."""
    name = (str(raw_name or "")).strip()
    if not name:
        raise EmployeeValidationError("name required")
    return name


def list_employees(config: Mapping[str, Any]) -> Sequence[Dict[str, Any]]:
    """Return the employee collection."""
    return employees_repository.fetch_all(config)


def create_employee(config: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Create an employee after validating input."""
    name = _validate_employee_name(payload.get("name"))
    employee_id = employees_repository.insert_employee(config, name)
    return {"id": employee_id, "name": name}
