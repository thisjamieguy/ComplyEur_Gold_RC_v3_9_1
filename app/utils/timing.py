import time
import logging
from typing import Optional


def init_request_timing(app, header_name: str = "X-Response-Time-ms") -> None:
    """Attach before/after request hooks to log and expose response times.

    Enabled by app factory when REQUEST_TIMING=true (env), to avoid overhead by default.
    """
    logger = logging.getLogger("request-timing")

    @app.before_request
    def _start_timer():
        from flask import g
        g._rt_start = time.perf_counter()

    @app.after_request
    def _stop_timer(response):
        from flask import g, request
        start: Optional[float] = getattr(g, "_rt_start", None)
        if start is not None:
            duration_ms = (time.perf_counter() - start) * 1000.0
            # Append header for quick visibility in browser/devtools
            try:
                response.headers[header_name] = f"{duration_ms:.2f}"
            except Exception:
                pass
            # Structured log line
            logger.info(
                "path=%s method=%s status=%s duration_ms=%.2f",
                request.path,
                request.method,
                response.status_code,
                duration_ms,
            )
        return response



