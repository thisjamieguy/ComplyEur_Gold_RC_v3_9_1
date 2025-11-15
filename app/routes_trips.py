"""Minimal Trips API endpoints for testing.

This provides a simplified CRUD API for trips that works alongside
the existing calendar API and main routes.
"""

from flask import Blueprint, request, jsonify

from app.services import trips_service
from app.services.trips_service import TripNotFoundError, TripValidationError

from .util_auth import login_required

trips_bp = Blueprint("trips", __name__)


def _success(payload, status_code=200):
    return jsonify(payload), status_code


@trips_bp.route("/trips", methods=["POST"])
@login_required
def create_trip():
    """Create a new trip."""
    data = request.get_json(force=True) or {}
    try:
        result = trips_service.create_trip(data)
    except TripValidationError as exc:
        return _success({"error": str(exc)}, 400)
    return _success(result, 201)


@trips_bp.route("/trips", methods=["GET"])
@login_required
def list_trips():
    """List all trips."""
    trips = trips_service.list_trips()
    return _success(trips)


@trips_bp.route("/trips/<int:trip_id>", methods=["PATCH"])
@login_required
def update_trip(trip_id):
    """Update an existing trip."""
    data = request.get_json(force=True) or {}
    try:
        trip = trips_service.update_trip(trip_id, data)
    except TripValidationError as exc:
        return _success({"error": str(exc)}, 400)
    except TripNotFoundError as exc:
        return _success({"error": str(exc)}, 404)
    return _success(trip)


@trips_bp.route("/trips/<int:trip_id>", methods=["DELETE"])
@login_required
def delete_trip(trip_id):
    """Delete a trip."""
    try:
        trips_service.delete_trip(trip_id)
    except TripNotFoundError as exc:
        return _success({"error": str(exc)}, 404)
    return _success({"success": True})
