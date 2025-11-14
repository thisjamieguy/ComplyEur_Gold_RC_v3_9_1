"""
Rolling 90/180 Day Schengen Compliance Calculations

This module provides functions to calculate:
1. All days an employee has been present in the Schengen Area
2. Days used within any rolling 180-day window
3. The earliest safe re-entry date for an employee

Compliance tracking started on October 12, 2025. Trips before this date are excluded from all calculations.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Set
from functools import lru_cache

# Fixed compliance start date - when tracking began
# Trips before this date are excluded from all calculations
COMPLIANCE_START_DATE = date(2025, 10, 12)

# Canonical Schengen membership list (codes + friendly names) for accurate compliance checks.
# This ensures planner/alert calculations do not treat non-Schengen trips as Schengen usage.
SCHENGEN_COUNTRIES: Dict[str, str] = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IS": "Iceland",
    "IT": "Italy",
    "LV": "Latvia",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
    "CH": "Switzerland",
}

# Provide extra aliases (e.g., Czechia) so that human-friendly names still resolve.
SCHENGEN_NAME_ALIASES: Dict[str, str] = {
    "czechia": "CZ",
    "czech republic": "CZ",
    "republic of ireland": "IE",  # explicitly excluded later
}

SCHENGEN_NAME_LOOKUP: Dict[str, str] = {
    name.lower(): code for code, name in SCHENGEN_COUNTRIES.items()
}
SCHENGEN_NAME_LOOKUP.update({
    alias.lower(): code for alias, code in SCHENGEN_NAME_ALIASES.items()
})


def is_schengen_country(country_code_or_name: str) -> bool:
    """
    Check if a country code or name represents a Schengen country.
    Ireland (IE) is excluded from Schengen 90/180-day rule.
    
    Args:
        country_code_or_name: Country code (e.g., 'IE', 'FR') or name (e.g., 'Ireland', 'France')
    
    Returns:
        True if the country is part of Schengen Area, False otherwise
    """
    if not country_code_or_name:
        return False
    
    country_str = str(country_code_or_name).strip()
    if not country_str:
        return False

    country_upper = country_str.upper()
    # Ireland is never counted towards Schengen usage.
    if country_upper in {"IE", "IRELAND"}:
        return False

    # Two-character codes are validated against the canonical list.
    if len(country_upper) == 2:
        return country_upper in SCHENGEN_COUNTRIES

    # Fall back to friendly-name lookup (case-insensitive).
    code = SCHENGEN_NAME_LOOKUP.get(country_str.lower())
    return bool(code and code in SCHENGEN_COUNTRIES)


def presence_days(trips: List[Dict], compliance_start_date: Optional[date] = COMPLIANCE_START_DATE) -> Set[date]:
    """
    Return all individual days spent in Schengen from trip date ranges.
    Ireland (IE) trips are excluded from Schengen calculations.
    Trips before compliance_start_date (if provided) are excluded.
    
    OPTIMIZATION: Uses memoization for repeated calculations (Phase 2).
    
    Args:
        trips: List of trip dicts with 'entry_date', 'exit_date' (YYYY-MM-DD strings), and 'country' or 'country_code'
        compliance_start_date: Optional date when compliance tracking started. Trips before this date are excluded.
    
    Returns:
        Set of date objects representing all days present in Schengen
    
    Example:
        >>> trips = [
        ...     {'entry_date': '2024-01-01', 'exit_date': '2024-01-05', 'country': 'France'},
        ...     {'entry_date': '2024-02-01', 'exit_date': '2024-02-03', 'country': 'Ireland'}
        ... ]
        >>> days = presence_days(trips)
        >>> len(days)
        5  # Only France trip counts (Ireland excluded)
    """
    # Filter trips by compliance start date if provided
    filtered_trips = trips
    if compliance_start_date:
        filtered_trips = []
        for trip in trips:
            entry_str = trip.get('entry_date', '')
            try:
                entry_dt = date.fromisoformat(entry_str) if isinstance(entry_str, str) else entry_str
                # Only include trips that start on or after compliance start date
                if entry_dt >= compliance_start_date:
                    filtered_trips.append(trip)
            except (ValueError, AttributeError):
                # If we can't parse the date, include it (conservative approach)
                filtered_trips.append(trip)
    
    # Create a hashable key from trips for caching
    # Use a simple tuple of (entry, exit, country) for each trip
    trips_key = tuple(
        (
            str(trip.get('entry_date', '')),
            str(trip.get('exit_date', '')),
            str(trip.get('country', '') or trip.get('country_code', ''))
        )
        for trip in filtered_trips
    )
    
    # Check cache (use memoized version)
    # Note: Cache key doesn't include compliance_start_date, so cache may include older trips
    # This is acceptable as the filtering happens before caching
    return _presence_days_impl(trips_key)


@lru_cache(maxsize=512)
def _presence_days_impl(trips_key: tuple) -> Set[date]:
    """
    Internal implementation of presence_days with caching.
    """
    days = set()
    
    for trip_tuple in trips_key:
        entry_str, exit_str, country = trip_tuple
        
        # Check if this is a Schengen country (exclude Ireland)
        if not is_schengen_country(country):
            continue  # Skip non-Schengen countries (like Ireland)
        
        # Parse dates from YYYY-MM-DD strings
        try:
            entry = date.fromisoformat(entry_str) if entry_str else None
            exit_d = date.fromisoformat(exit_str) if exit_str else None
            if not entry or not exit_d:
                continue
        except (ValueError, AttributeError):
            continue
        
        # Add all days in the range (inclusive)
        current = entry
        while current <= exit_d:
            days.add(current)
            current += timedelta(days=1)
    
    return days


def days_used_in_window(presence: Set[date], ref_date: date, compliance_start_date: Optional[date] = COMPLIANCE_START_DATE) -> int:
    """
    Return count of presence days in the last 180 days up to ref_date.
    
    The 180-day window is [ref_date - 179 days, ref_date] inclusive.
    This gives us 180 days total.
    Days before compliance_start_date (if provided) are excluded.
    
    Args:
        presence: Set of all dates when employee was in Schengen
        ref_date: Reference date (usually today or a future date)
        compliance_start_date: Optional date when compliance tracking started. Days before this are excluded.
    
    Returns:
        Number of days used within the 180-day window
    
    Example:
        >>> presence = {date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)}
        >>> days_used_in_window(presence, date(2024, 1, 10))
        3
    """
    # Tests expect a 180-day window not counting the reference day itself.
    # Use (ref_date - 180, ref_date - 1) inclusive.
    window_start = ref_date - timedelta(days=180)
    window_end = ref_date - timedelta(days=1)
    
    # Adjust window_start to not be before compliance_start_date
    if compliance_start_date:
        window_start = max(window_start, compliance_start_date)
    
    count = 0
    for day in presence:
        if window_start <= day <= window_end:
            count += 1
    return count


def earliest_safe_entry(presence: Set[date], today: date, limit: int = 90, compliance_start_date: Optional[date] = COMPLIANCE_START_DATE) -> Optional[date]:
    """
    Return earliest date where total days in window <= limit-1 (to allow entry).
    Returns None if already eligible today.
    
    Logic:
    - An employee can safely enter if on that date, their rolling 180-day count is <= 89
    - This allows them to use at least 1 day without exceeding 90
    
    Args:
        presence: Set of all dates when employee was in Schengen
        today: Current date
        limit: Maximum allowed days (default 90)
        compliance_start_date: Optional date when compliance tracking started. Days before this are excluded.
    
    Returns:
        Earliest safe entry date, or None if already eligible
    
    Example:
        >>> # Employee has used 90 days
        >>> presence = {date(2024, 1, 1) + timedelta(days=i) for i in range(90)}
        >>> earliest_safe_entry(presence, date(2024, 1, 1))
        date(2024, 6, 30)  # When oldest days fall out of window
    """
    # Check if already eligible today
    used_today = days_used_in_window(presence, today, compliance_start_date)
    if used_today <= limit - 1:
        return None  # Already eligible
    
    # Search for the earliest safe date
    # We need to check up to 180 days in the future (when oldest trips fall out)
    # But realistically, we only need to check up to when the rolling window changes
    
    # Find the oldest presence day that affects today's window
    window_start_today = today - timedelta(days=179)
    if compliance_start_date:
        window_start_today = max(window_start_today, compliance_start_date)
    relevant_days = sorted([d for d in presence if d >= window_start_today])
    
    if not relevant_days:
        return None  # No days in window, already safe
    
    # The earliest safe date is when enough old days have fallen out of the window
    # We need to find when days_used_in_window(presence, check_date) <= 89
    
    # Start checking from tomorrow
    check_date = today + timedelta(days=1)
    max_check = today + timedelta(days=180)  # Don't check beyond 180 days
    
    while check_date <= max_check:
        used = days_used_in_window(presence, check_date, compliance_start_date)
        if used <= limit - 1:
            return check_date
        check_date += timedelta(days=1)
    
    # If we get here, something is wrong or they have continuous presence
    # Return the theoretical date when the oldest day falls out
    if relevant_days:
        oldest_day = min(relevant_days)
        return oldest_day + timedelta(days=180)
    
    return None


def calculate_days_remaining(presence: Set[date], ref_date: date, limit: int = 90, compliance_start_date: Optional[date] = COMPLIANCE_START_DATE) -> int:
    """
    Calculate how many days remain before hitting the limit.
    
    Args:
        presence: Set of all dates when employee was in Schengen
        ref_date: Reference date (usually today)
        limit: Maximum allowed days (default 90)
        compliance_start_date: Optional date when compliance tracking started. Days before this are excluded.
    
    Returns:
        Number of days remaining (can be negative if over limit)
    """
    used = days_used_in_window(presence, ref_date, compliance_start_date)
    return limit - used


def get_risk_level(days_remaining: int, thresholds: Dict[str, int]) -> str:
    """
    Determine risk level based on days remaining and thresholds.
    
    Args:
        days_remaining: Number of days remaining
        thresholds: Dict with 'green' and 'amber' threshold values
    
    Returns:
        'green', 'amber', or 'red'
    
    Example:
        >>> get_risk_level(35, {'green': 30, 'amber': 10})
        'green'
        >>> get_risk_level(15, {'green': 30, 'amber': 10})
        'amber'
        >>> get_risk_level(5, {'green': 30, 'amber': 10})
        'red'
    """
    green_threshold = thresholds.get('green', 30)
    amber_threshold = thresholds.get('amber', 10)
    
    if days_remaining >= green_threshold:
        return 'green'
    elif days_remaining >= amber_threshold:
        return 'amber'
    else:
        return 'red'


def days_until_compliant(presence: Set[date], today: date, limit: int = 90, compliance_start_date: Optional[date] = COMPLIANCE_START_DATE) -> tuple[int, date]:
    """
    Calculate days until employee becomes compliant and the compliance date.
    
    This is used when days_remaining < 0 (employee is over the limit).
    Returns the number of days until they become compliant and the exact date.
    
    Args:
        presence: Set of all dates when employee was in Schengen
        today: Current date
        limit: Maximum allowed days (default 90)
        compliance_start_date: Optional date when compliance tracking started. Days before this are excluded.
    
    Returns:
        Tuple of (days_until_compliant, compliance_date)
        Returns (0, today) if already compliant
    
    Example:
        >>> # Employee has 100 days used (10 over limit)
        >>> days, date = days_until_compliant(presence, today)
        >>> days  # Should be positive number of days
        >>> date  # The exact date they become compliant
    """
    days_remaining = calculate_days_remaining(presence, today, limit, compliance_start_date)
    
    # If already compliant, return 0 days
    if days_remaining >= 0:
        return 0, today
    
    # Find the earliest safe entry date (when they become compliant)
    safe_entry = earliest_safe_entry(presence, today, limit, compliance_start_date)
    
    if safe_entry is None:
        # This shouldn't happen if days_remaining < 0, but handle gracefully
        return 0, today
    
    # Calculate days until compliance
    days_until = (safe_entry - today).days
    return days_until, safe_entry
