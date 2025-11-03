import os, re
from datetime import datetime
from argon2 import PasswordHasher, exceptions as argon_exc
from zxcvbn import zxcvbn
from flask import session, current_app


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

