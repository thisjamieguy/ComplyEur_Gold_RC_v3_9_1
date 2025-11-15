"""Compatibility layer that re-exports the unified ComplyEur factory."""

from .__init__ import create_app, db, csrf, limiter

__all__ = ['create_app', 'db', 'csrf', 'limiter']
