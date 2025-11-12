import logging
import os
import re
from datetime import datetime
from argon2 import PasswordHasher, exceptions as argon_exc
from flask import session, current_app

try:
    from zxcvbn import zxcvbn as _zxcvbn
except ImportError:
    _zxcvbn = None

logger = logging.getLogger(__name__)


def _fallback_zxcvbn(password: str) -> dict:
    """Lightweight heuristic when zxcvbn is unavailable."""
    length = len(password)
    score = 4 if length >= 16 else 3 if length >= 12 else 1
    feedback = {
        "warning": "Install zxcvbn-python for advanced strength checks.",
        "suggestions": [
            "Use a longer passphrase with mixed character types.",
            "Avoid common words and repeated patterns."
        ],
    }
    return {"score": score, "feedback": feedback}


if _zxcvbn is None:
    logger.warning("zxcvbn-python not installed; using heuristic password strength checks")


def zxcvbn(password: str) -> dict:
    """Wrapper to ensure password strength scoring is always available."""
    if _zxcvbn is not None:
        return _zxcvbn(password)
    return _fallback_zxcvbn(password)


def get_hasher():
    return PasswordHasher(
        time_cost=current_app.config["ARGON2_TIME"],
        memory_cost=current_app.config["ARGON2_MEMORY"],
        parallelism=current_app.config["ARGON2_PARALLELISM"]
    )


def hash_password(plain: str) -> str:
    if len(plain) < 12:
        raise ValueError("Password too short (min 12).")
    if zxcvbn(plain)["score"] < 3:
        raise ValueError("Password too weak (use a longer passphrase).")
    return get_hasher().hash(plain)


def verify_password(hash_str: str, plain: str) -> bool:
    try:
        return get_hasher().verify(hash_str, plain)
    except argon_exc.VerifyMismatchError:
        return False


def rotate_session_id():
    # Flask regenerates session by changing contents
    session.modified = True
    session["issued_at"] = datetime.utcnow().timestamp()
    session["last_seen"] = session["issued_at"]


def session_expired():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    issued = session.get("issued_at")
    last = session.get("last_seen")
    if not issued or not last:
        return True
    idle = now.timestamp() - last
    absolute = now.timestamp() - issued
    return (idle > current_app.config["IDLE_TIMEOUT"].total_seconds()
            or absolute > current_app.config["ABSOLUTE_TIMEOUT"].total_seconds())


def touch_session():
    from datetime import datetime
    session["last_seen"] = datetime.utcnow().timestamp()
