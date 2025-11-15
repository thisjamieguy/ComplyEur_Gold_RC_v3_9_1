"""Health status service helpers for ComplyEur.

Centralises uptime/version calculations so route handlers stay lean and we can
extend this logic (e.g. caching, dependency probes, async checks) in Phase 4+.
"""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional

DEFAULT_STATUS = "healthy"
DEFAULT_VERSION = "unknown"
APP_START_TS_KEY = "APP_START_TS"
APP_VERSION_KEY = "APP_VERSION"


def _resolve_uptime_seconds(config: Mapping[str, Any], *, now: Optional[float] = None) -> int:
    """Return uptime in seconds, matching the legacy behaviour."""
    reference_now = now or time.time()
    start_ts = config.get(APP_START_TS_KEY, reference_now)
    try:
        start_float = float(start_ts)
    except (TypeError, ValueError):
        start_float = reference_now
    return int(reference_now - start_float)


def build_health_payload(
    config: Mapping[str, Any],
    *,
    check: Optional[str] = None,
    now: Optional[float] = None,
) -> dict[str, Any]:
    """Compose the common health payload dictionary."""
    payload: dict[str, Any] = {
        "status": DEFAULT_STATUS,
        "uptime_seconds": _resolve_uptime_seconds(config, now=now),
        "version": str(config.get(APP_VERSION_KEY, DEFAULT_VERSION)),
    }
    if check:
        payload["check"] = check
    return payload


def get_version_payload(config: Mapping[str, Any]) -> dict[str, str]:
    """Expose the API version payload."""
    return {"version": str(config.get(APP_VERSION_KEY, DEFAULT_VERSION))}
