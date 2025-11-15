"""Minimal Employees API endpoints for testing.

This provides a simplified CRUD API for employees that works alongside
the existing calendar API and main routes.
"""

from flask import Blueprint, request, jsonify, current_app

from app.services import employees_service
from app.services.employees_service import EmployeeValidationError

from .util_auth import login_required

employees_bp = Blueprint("employees", __name__)


def _success(payload, status_code=200):
    return jsonify(payload), status_code


@employees_bp.route("/employees", methods=["GET"])
@login_required
def list_employees():
    """List all employees."""
    employees = employees_service.list_employees(current_app.config)
    return _success(employees)


@employees_bp.route("/employees", methods=["POST"])
@login_required
def create_employee():
    """Create a new employee."""
    data = request.get_json(force=True) or {}
    try:
        employee = employees_service.create_employee(current_app.config, data)
    except EmployeeValidationError as exc:
        return _success({"error": str(exc)}, status_code=400)
    return _success(employee, status_code=201)
