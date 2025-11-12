"""
Cache invalidation utilities for ComplyEur.

Provides functions to invalidate cached responses when data changes.
"""

import logging
from flask import current_app

logger = logging.getLogger(__name__)


def invalidate_dashboard_cache():
    """
    Invalidate all dashboard cache entries.
    
    Called when trips or employees are added/updated/deleted.
    """
    cache = current_app.config.get('CACHE')
    if not cache:
        return
    
    try:
        # Clear all dashboard cache entries
        # Flask-Caching SimpleCache doesn't support pattern-based clearing,
        # so we'll need to track keys or clear all
        cache.clear()
        logger.info("Dashboard cache invalidated")
    except Exception as e:
        logger.warning(f"Failed to invalidate dashboard cache: {e}")


def invalidate_employee_cache(employee_id: int):
    """
    Invalidate cache entries related to a specific employee.
    
    Args:
        employee_id: ID of the employee whose cache should be invalidated
    """
    cache = current_app.config.get('CACHE')
    if not cache:
        return
    
    try:
        # For SimpleCache, we clear all (could be optimized with key tracking)
        cache.clear()
        logger.info(f"Cache invalidated for employee {employee_id}")
    except Exception as e:
        logger.warning(f"Failed to invalidate employee cache: {e}")

