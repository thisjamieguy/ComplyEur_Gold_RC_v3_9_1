"""Trips domain orchestration."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping

from app.repositories import trips_repository


class TripValidationError(ValueError):
    """Raised when incoming trip payloads are invalid."""


class TripNotFoundError(LookupError):
    """Raised when a trip cannot be located."""


def _validate_create_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    employee_id = payload.get("employee_id")
    country = (payload.get("country") or "").strip()
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    if not all([employee_id, country, start_date, end_date]):
        raise TripValidationError("missing fields")

    validated = dict(payload)
    validated["country"] = country
    return validated


def list_trips() -> list[Dict[str, Any]]:
    """Return trips with API-shaped fields."""
    return trips_repository.fetch_all()


def create_trip(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Create a trip after validation."""
    validated = _validate_create_payload(payload)
    trip_id = trips_repository.insert_trip(validated)
    return {"id": trip_id}


def _build_update_columns(payload: Mapping[str, Any]) -> MutableMapping[str, Any]:
    updates: MutableMapping[str, Any] = {}
    if "start_date" in payload:
        updates["entry_date"] = payload["start_date"]
    if "end_date" in payload:
        updates["exit_date"] = payload["end_date"]
    if "country" in payload:
        updates["country"] = payload["country"]
    if "employee_id" in payload:
        updates["employee_id"] = payload["employee_id"]
    return updates


def update_trip(trip_id: int, payload: Mapping[str, Any]) -> Dict[str, Any]:
    updates = _build_update_columns(payload)
    if not updates:
        raise TripValidationError("No fields to update")
    updated_rows = trips_repository.update_trip(trip_id, updates)
    if not updated_rows:
        raise TripNotFoundError("Trip not found")
    trip = trips_repository.fetch_by_id(trip_id)
    if trip is None or not trip.get("id"):
        raise TripNotFoundError("Trip not found")
    return trip


def delete_trip(trip_id: int) -> None:
    deleted = trips_repository.delete_trip(trip_id)
    if not deleted:
        raise TripNotFoundError("Trip not found")
