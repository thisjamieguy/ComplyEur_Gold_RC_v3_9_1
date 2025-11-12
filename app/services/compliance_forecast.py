"""
Future Job Compliance Forecast Service

This module provides functions to forecast compliance issues for future scheduled jobs
based on the 90/180 day EU rolling window rule, considering both past trips and other
scheduled future trips.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from .rolling90 import (
    presence_days, 
    days_used_in_window, 
    earliest_safe_entry, 
    calculate_days_remaining,
    is_schengen_country
)


def get_risk_level_for_forecast(days_used: int, warning_threshold: int = 80) -> str:
    """
    Determine risk level for future jobs based on days used.
    
    Args:
        days_used: Number of days that will be used when job starts
        warning_threshold: Threshold for yellow warning (default 80)
    
    Returns:
        'green', 'yellow', or 'red'
    """
    if days_used >= 90:
        return 'red'  # Would exceed limit
    elif days_used >= warning_threshold:
        return 'yellow'  # Approaching limit
    else:
        return 'green'  # Safe


def calculate_compliant_from_date(
    all_trips: List[Dict],
    future_job: Dict,
    limit: int = 90
) -> Optional[date]:
    """
    Calculate the date when an employee will become compliant for a future job.
    
    This is the date when enough old trips have "aged out" of the 180-day window
    to allow the future job to be compliant.
    
    Args:
        all_trips: List of all trips (past and future)
        future_job: The future job that would be non-compliant
        limit: Maximum allowed days (default 90)
    
    Returns:
        Date when employee will be compliant, or None if already compliant
    """
    job_start = date.fromisoformat(future_job['entry_date']) if isinstance(future_job['entry_date'], str) else future_job['entry_date']
    job_end = date.fromisoformat(future_job['exit_date']) if isinstance(future_job['exit_date'], str) else future_job['exit_date']
    job_duration = (job_end - job_start).days + 1
    
    # Get all presence days from trips BEFORE this job
    trips_before_job = [t for t in all_trips if date.fromisoformat(t['entry_date'] if isinstance(t['entry_date'], str) else str(t['entry_date'])) < job_start]
    presence = presence_days(trips_before_job)
    
    # Check each day from job_start onwards to find when it becomes compliant
    check_date = job_start
    max_check = job_start + timedelta(days=180)  # Don't check beyond 180 days
    
    while check_date <= max_check:
        days_used_at_check = days_used_in_window(presence, check_date)
        
        # If adding the job duration would be compliant, this is the date
        if days_used_at_check + job_duration <= limit:
            return check_date
        
        check_date += timedelta(days=1)
    
    # If still not compliant after 180 days, return the theoretical date
    return max_check


def calculate_future_job_compliance(
    employee_id: int,
    future_job: Dict,
    all_employee_trips: List[Dict],
    warning_threshold: int = 80,
    limit: int = 90
) -> Dict:
    """
    Calculate compliance status for a future job.
    
    This function considers:
    - All past trips (what's already happened)
    - All future trips scheduled BEFORE this job
    - The duration of the job itself
    
    Args:
        employee_id: ID of the employee
        future_job: Dict with 'entry_date', 'exit_date', 'country'
        all_employee_trips: List of all trips for this employee (past and future)
        warning_threshold: Days threshold for yellow warning (default 80)
        limit: Maximum allowed days (default 90)
    
    Returns:
        Dict containing:
        - job: The original job dict
        - job_start_date: Date object for job start
        - job_end_date: Date object for job end
        - job_duration: Number of days the job spans
        - days_used_before_job: Days used in 180-day window before job starts
        - days_after_job: Days that will be used after adding this job
        - days_remaining_after_job: Days remaining after this job
        - risk_level: 'green', 'yellow', or 'red'
        - is_compliant: Boolean if job would be compliant
        - compliant_from_date: Date when job becomes compliant (if not compliant), or None
        - trips_in_window: List of trips that contribute to the calculation
    """
    # Parse job dates
    job_start = date.fromisoformat(future_job['entry_date']) if isinstance(future_job['entry_date'], str) else future_job['entry_date']
    job_end = date.fromisoformat(future_job['exit_date']) if isinstance(future_job['exit_date'], str) else future_job['exit_date']
    job_duration = (job_end - job_start).days + 1
    
    # Only count if it's a Schengen country
    job_country = future_job.get('country') or future_job.get('country_code', '')
    is_job_schengen = is_schengen_country(job_country)
    
    # Get all trips BEFORE this job starts
    trips_before_job = [
        t for t in all_employee_trips 
        if date.fromisoformat(t['entry_date'] if isinstance(t['entry_date'], str) else str(t['entry_date'])) < job_start
    ]
    
    # Calculate presence days from trips before the job
    presence = presence_days(trips_before_job)
    
    # Calculate days used in 180-day window at job start date
    days_used_before = days_used_in_window(presence, job_start)
    
    # Calculate days after adding this job (only if Schengen)
    days_after = days_used_before + (job_duration if is_job_schengen else 0)
    days_remaining = limit - days_after
    
    # Determine risk level
    risk_level = get_risk_level_for_forecast(days_after, warning_threshold)
    is_compliant = days_after <= limit
    
    # If not compliant, calculate when it would be compliant
    compliant_from = None
    if not is_compliant and is_job_schengen:
        compliant_from = calculate_compliant_from_date(all_employee_trips, future_job, limit)
    
    # Find trips that contribute to the window (for detailed breakdown)
    window_start = job_start - timedelta(days=179)
    trips_in_window = [
        t for t in trips_before_job
        if date.fromisoformat(t['exit_date'] if isinstance(t['exit_date'], str) else str(t['exit_date'])) >= window_start
    ]
    
    return {
        'employee_id': employee_id,
        'job': future_job,
        'job_start_date': job_start,
        'job_end_date': job_end,
        'job_duration': job_duration,
        'days_used_before_job': days_used_before,
        'days_after_job': days_after,
        'days_used_after_job': days_after,
        'days_remaining_after_job': days_remaining,
        'risk_level': risk_level,
        'is_compliant': is_compliant,
        'is_schengen': is_job_schengen,
        'compliant_from_date': compliant_from,
        'trips_in_window': trips_in_window
    }


def get_all_future_jobs_for_employee(
    employee_id: int,
    all_trips: List[Dict],
    warning_threshold: int = 80
) -> List[Dict]:
    """
    Get compliance forecast for all future jobs for an employee.
    
    Args:
        employee_id: ID of the employee
        all_trips: List of all trips for this employee
        warning_threshold: Days threshold for yellow warning
    
    Returns:
        List of compliance forecasts for each future job
    """
    today = date.today()
    
    # Separate future and past trips
    future_trips = [t for t in all_trips if date.fromisoformat(t['entry_date'] if isinstance(t['entry_date'], str) else str(t['entry_date'])) > today]
    
    # Sort future trips by entry date
    future_trips.sort(key=lambda t: t['entry_date'])
    
    forecasts = []
    for future_job in future_trips:
        forecast = calculate_future_job_compliance(
            employee_id,
            future_job,
            all_trips,
            warning_threshold
        )
        forecasts.append(forecast)
    
    return forecasts


def calculate_what_if_scenario(
    employee_id: int,
    all_trips: List[Dict],
    scenario_start: date,
    scenario_end: date,
    scenario_country: str,
    warning_threshold: int = 80
) -> Dict:
    """
    Calculate a "what-if" scenario for a potential future trip.
    
    This allows admins to test if a potential trip would be compliant
    before actually scheduling it.
    
    Args:
        employee_id: ID of the employee
        all_trips: List of all existing trips for this employee
        scenario_start: Start date of the hypothetical trip
        scenario_end: End date of the hypothetical trip
        scenario_country: Country code for the hypothetical trip
        warning_threshold: Days threshold for yellow warning
    
    Returns:
        Compliance forecast dict for the scenario
    """
    # Create a hypothetical trip dict
    hypothetical_trip = {
        'entry_date': str(scenario_start),
        'exit_date': str(scenario_end),
        'country': scenario_country
    }
    
    return calculate_future_job_compliance(
        employee_id,
        hypothetical_trip,
        all_trips,
        warning_threshold
    )

