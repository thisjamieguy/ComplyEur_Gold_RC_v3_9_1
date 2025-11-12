"""
Caching utilities for ComplyEur performance optimization.

Provides helper functions for caching expensive operations like compliance calculations.
"""

from functools import lru_cache, wraps
from typing import Callable, Any, Tuple
from datetime import date
import hashlib
import json


def cache_key_for_trips(trips: list, ref_date: date) -> str:
    """
    Generate a cache key for trip-based calculations.
    
    Args:
        trips: List of trip dictionaries
        ref_date: Reference date for calculations
    
    Returns:
        Cache key string
    """
    # Create a stable representation of trips for hashing
    trips_str = json.dumps(sorted([
        {
            'entry_date': str(t.get('entry_date', '')),
            'exit_date': str(t.get('exit_date', '')),
            'country': str(t.get('country', ''))
        }
        for t in trips
    ], key=lambda x: (x['entry_date'], x['exit_date'])), sort_keys=True)
    
    key_data = f"{trips_str}:{ref_date.isoformat()}"
    return hashlib.md5(key_data.encode()).hexdigest()


def memoize_compliance_calc(func: Callable) -> Callable:
    """
    Decorator to memoize expensive compliance calculations.
    
    Uses LRU cache with hashable trip data.
    """
    @lru_cache(maxsize=256)
    def cached_func(trips_tuple: Tuple[Tuple[str, str, str], ...], ref_date_str: str) -> Any:
        """Cached wrapper that converts tuples back to trip dicts."""
        # Convert tuple representation back to list of dicts
        trips = [
            {
                'entry_date': trip[0],
                'exit_date': trip[1],
                'country': trip[2]
            }
            for trip in trips_tuple
        ]
        ref_date = date.fromisoformat(ref_date_str)
        return func(trips, ref_date)
    
    @wraps(func)
    def wrapper(trips: list, ref_date: date) -> Any:
        """Wrapper that converts trips to hashable format."""
        # Convert trips to hashable tuple format
        trips_tuple = tuple(
            (
                str(t.get('entry_date', '')),
                str(t.get('exit_date', '')),
                str(t.get('country', ''))
            )
            for t in trips
        )
        ref_date_str = ref_date.isoformat()
        return cached_func(trips_tuple, ref_date_str)
    
    return wrapper


def clear_compliance_cache():
    """Clear all compliance calculation caches."""
    # This would clear all LRU caches if needed
    # For now, we rely on maxsize limits
    pass

