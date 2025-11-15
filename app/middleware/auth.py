"""Authentication middleware helpers for ComplyEur."""

from __future__ import annotations

import os
from functools import wraps
from types import SimpleNamespace
from typing import Any, Callable, TypeVar, cast

from flask import (
    current_app,
    g,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)

from app.modules.auth import SessionManager

F = TypeVar("F", bound=Callable[..., Any])


def wants_json_response() -> bool:
    """Detect whether the current request expects a JSON response."""
    accept = request.headers.get("Accept", "")
    return (
        request.is_json
        or "application/json" in accept
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def _unauthorised(expired: bool = False):
    """Return a consistent unauthorised response."""
    message = "Session expired" if expired else "Authentication required"
    if wants_json_response():
        return jsonify({"error": message, "redirect": url_for("auth.login")}), 401
    return redirect(url_for("auth.login"))


def current_user(reload: bool = False):
    """Return the SQLAlchemy user associated with the current session."""
    if not reload and hasattr(g, "_current_user"):
        return getattr(g, "_current_user")

    user_id = session.get("user_id")
    if not user_id:
        g._current_user = None
        return None

    from app import models_auth

    user = None
    try:
        user = models_auth.User.query.get(user_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.error("Failed to load user %s: %s", user_id, exc)
    if not user and os.getenv("EUTRACKER_BYPASS_LOGIN") == "1":
        user = SimpleNamespace(id=user_id, username="admin", role="admin")
    g._current_user = user
    return user


def _ensure_bypass_session():
    """Apply developer login bypass if enabled."""
    if os.getenv("EUTRACKER_BYPASS_LOGIN") == "1" and not session.get("user_id"):
        SessionManager.set_user(1, "admin")
        session.permanent = True


def login_required(func: F) -> F:
    """Decorator ensuring the requester is authenticated."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        _ensure_bypass_session()

        user_id = session.get("user_id")
        if not user_id:
            return _unauthorised()

        try:
            if SessionManager.is_expired():
                SessionManager.clear_session()
                return _unauthorised(expired=True)
            SessionManager.touch_session()
            session.permanent = True
        except Exception as exc:
            current_app.logger.error("Session enforcement failed: %s", exc)
            SessionManager.clear_session()
            return _unauthorised(expired=True)

        user = current_user()
        if not user:
            SessionManager.clear_session()
            return _unauthorised()

        return func(*args, **kwargs)

    return cast(F, wrapper)


__all__ = ["login_required", "current_user", "wants_json_response"]
