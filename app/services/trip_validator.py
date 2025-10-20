"""
Trip Validation Module

This module validates trips for:
1. Hard errors (blocks save): date logic errors, overlaps
2. Soft warnings (allow with override): missing exit date, long trips
"""

from datetime import date, timedelta
from typing import List, Dict, Tuple


def validate_trip(
    existing_trips: List[Dict],
    new_entry_date: date,
    new_exit_date: date = None,
    trip_id_to_exclude: int = None
) -> Tuple[List[str], List[str]]:
    """
    Validate a trip against business rules.
    
    Args:
        existing_trips: List of existing trip dicts with 'id', 'entry_date', 'exit_date'
        new_entry_date: Entry date of the new/edited trip
        new_exit_date: Exit date of the new/edited trip (None for ongoing)
        trip_id_to_exclude: ID of trip being edited (to exclude from overlap check)
    
    Returns:
        Tuple of (hard_errors, soft_warnings)
        - hard_errors: List of blocking error messages
        - soft_warnings: List of warning messages (can be overridden)
    
    Example:
        >>> existing = [
        ...     {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'}
        ... ]
        >>> errors, warnings = validate_trip(existing, date(2024, 1, 5), date(2024, 1, 15))
        >>> errors
        ['Trip dates overlap with existing trip from 01-01-2024 to 10-01-2024']
    """
    hard_errors = []
    soft_warnings = []
    
    # Hard Error 1: Exit date before entry date
    if new_exit_date and new_exit_date < new_entry_date:
        hard_errors.append("Exit date cannot be before entry date")
        return hard_errors, soft_warnings  # Return early, other checks won't be valid
    
    # Soft Warning 1: Missing exit date (ongoing trip)
    if new_exit_date is None:
        soft_warnings.append("Trip has no exit date (ongoing trip)")
    
    # Soft Warning 2: Trip longer than 90 days
    if new_exit_date:
        duration = (new_exit_date - new_entry_date).days + 1
        if duration > 90:
            soft_warnings.append(f"Trip duration ({duration} days) exceeds 90 days")
    
    # Hard Error 2: Overlapping date ranges
    for trip in existing_trips:
        # Skip the trip being edited
        if trip_id_to_exclude and trip.get('id') == trip_id_to_exclude:
            continue
        
        # Parse existing trip dates
        if isinstance(trip.get('entry_date'), str):
            trip_entry = date.fromisoformat(trip['entry_date'])
        else:
            trip_entry = trip['entry_date']
        
        if isinstance(trip.get('exit_date'), str):
            trip_exit = date.fromisoformat(trip['exit_date'])
        else:
            trip_exit = trip['exit_date']
        
        # Check for overlap
        # Two date ranges overlap if: start1 <= end2 AND start2 <= end1
        if new_exit_date:
            if new_entry_date <= trip_exit and trip_entry <= new_exit_date:
                # Format dates for display
                trip_entry_str = trip_entry.strftime('%d-%m-%Y')
                trip_exit_str = trip_exit.strftime('%d-%m-%Y')
                hard_errors.append(
                    f"Trip dates overlap with existing trip from {trip_entry_str} to {trip_exit_str}"
                )
        else:
            # New trip has no exit date, check if entry overlaps with existing
            if new_entry_date <= trip_exit:
                trip_entry_str = trip_entry.strftime('%d-%m-%Y')
                trip_exit_str = trip_exit.strftime('%d-%m-%Y')
                hard_errors.append(
                    f"Trip entry date overlaps with existing trip from {trip_entry_str} to {trip_exit_str}"
                )
    
    return hard_errors, soft_warnings


def validate_date_range(entry_date: date, exit_date: date) -> Tuple[List[str], List[str]]:
    """
    Validate basic date range logic.
    
    Args:
        entry_date: Entry date
        exit_date: Exit date
    
    Returns:
        Tuple of (hard_errors, soft_warnings)
    """
    hard_errors: List[str] = []
    soft_warnings: List[str] = []

    if exit_date <= entry_date:
        hard_errors.append("Exit date must be after entry date")

    # Check for reasonable duration (max 2 years)
    if (exit_date - entry_date).days > 730:
        soft_warnings.append("Trip duration exceeds 2 years; verify this is intended")

    return hard_errors, soft_warnings


def check_trip_overlaps(
    trips: List[Dict],
    exclude_trip_id: int = None
) -> List[Tuple[Dict, Dict]]:
    """
    Check for any overlapping trips in a list.
    
    Args:
        trips: List of trip dicts with 'id', 'entry_date', 'exit_date'
        exclude_trip_id: Optional trip ID to exclude from checks
    
    Returns:
        List of tuples of overlapping trip pairs
    """
    overlaps = []
    
    for i, trip1 in enumerate(trips):
        if exclude_trip_id and trip1.get('id') == exclude_trip_id:
            continue
            
        for trip2 in trips[i+1:]:
            if exclude_trip_id and trip2.get('id') == exclude_trip_id:
                continue
            
            # Parse dates
            if isinstance(trip1.get('entry_date'), str):
                t1_entry = date.fromisoformat(trip1['entry_date'])
                t1_exit = date.fromisoformat(trip1['exit_date'])
            else:
                t1_entry = trip1['entry_date']
                t1_exit = trip1['exit_date']
            
            if isinstance(trip2.get('entry_date'), str):
                t2_entry = date.fromisoformat(trip2['entry_date'])
                t2_exit = date.fromisoformat(trip2['exit_date'])
            else:
                t2_entry = trip2['entry_date']
                t2_exit = trip2['exit_date']
            
            # Check overlap
            if t1_entry <= t2_exit and t2_entry <= t1_exit:
                overlaps.append((trip1, trip2))
    
    return overlaps


def format_validation_message(errors: List[str], warnings: List[str]) -> str:
    """
    Format validation errors and warnings into a user-friendly message.
    
    Args:
        errors: List of error messages
        warnings: List of warning messages
    
    Returns:
        Formatted HTML string
    """
    html = []
    
    if errors:
        html.append('<div class="validation-errors" style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; margin-bottom: 12px; border-radius: 4px;">')
        html.append('<strong style="color: #991b1b;">❌ Errors (must fix):</strong>')
        html.append('<ul style="margin: 8px 0 0 20px; color: #991b1b;">')
        for error in errors:
            html.append(f'<li>{error}</li>')
        html.append('</ul></div>')
    
    if warnings:
        html.append('<div class="validation-warnings" style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 4px;">')
        html.append('<strong style="color: #92400e;">⚠️ Warnings:</strong>')
        html.append('<ul style="margin: 8px 0 0 20px; color: #92400e;">')
        for warning in warnings:
            html.append(f'<li>{warning}</li>')
        html.append('</ul></div>')
    
    return ''.join(html)

