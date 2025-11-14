"""
Runtime environment helpers for ComplyEur.

Centralises:
- Required environment validation
- Persistent directory creation
- Database path normalisation
- Standard directory creation (uploads/logs/exports/backups)
- Shared log/audit file locations

All filesystem interactions (Flask runtime, importer, CLI, tests) should use
this module so behaviour is identical locally and on Render.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

REQUIRED_ENV_VARS = ("SECRET_KEY", "ADMIN_PASSWORD_HASH", "DATABASE_PATH", "PERSISTENT_DIR")
STANDARD_DIRECTORIES = {
    "uploads": "uploads",
    "logs": "logs",
    "exports": "exports",
    "backups": "backups",
}
LOG_FILE_NAME = "app.log"
AUDIT_LOG_NAME = "audit.log"


@dataclass(frozen=True)
class RuntimeState:
    """Represents the resolved runtime filesystem state."""

    persistent_dir: Path
    database_path: Path
    sqlalchemy_uri: str
    directories: Dict[str, Path]
    log_file: Path
    audit_log_file: Path


_STATE: Optional[RuntimeState] = None


def _env() -> Dict[str, str]:
    return os.environ


def require_env_vars(env: Optional[Dict[str, str]] = None) -> None:
    """Raise immediately if any required variable is missing or empty."""
    env = env or _env()
    missing = [var for var in REQUIRED_ENV_VARS if not env.get(var)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables for ComplyEur startup: "
            + ", ".join(sorted(missing))
        )


def _normalise_dir(path_value: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalise_database_path(raw_path: str, persistent_dir: Path) -> Path:
    cell = Path(raw_path.strip())
    if not cell.is_absolute():
        cell = persistent_dir / cell
    cell = cell.expanduser().resolve()
    cell.parent.mkdir(parents=True, exist_ok=True)
    return cell


def _touch_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    return path


def build_runtime_state(force_refresh: bool = False) -> RuntimeState:
    """Return cached runtime state (creating directories on first call)."""
    global _STATE
    if _STATE is not None and not force_refresh:
        return _STATE

    env = _env()
    require_env_vars(env)

    persistent_dir = _normalise_dir(env["PERSISTENT_DIR"])
    directories: Dict[str, Path] = {}
    for key, relative in STANDARD_DIRECTORIES.items():
        target = persistent_dir / relative
        target.mkdir(parents=True, exist_ok=True)
        directories[key] = target

    db_path = _normalise_database_path(env["DATABASE_PATH"], persistent_dir)
    env["DATABASE_PATH"] = str(db_path)
    sqlalchemy_uri = env.get("SQLALCHEMY_DATABASE_URI")
    if not sqlalchemy_uri:
        sqlalchemy_uri = f"sqlite:///{db_path}"
        env["SQLALCHEMY_DATABASE_URI"] = sqlalchemy_uri

    log_file = _touch_file(directories["logs"] / LOG_FILE_NAME)
    audit_log = _touch_file(directories["logs"] / AUDIT_LOG_NAME)

    _STATE = RuntimeState(
        persistent_dir=persistent_dir,
        database_path=db_path,
        sqlalchemy_uri=sqlalchemy_uri,
        directories=directories,
        log_file=log_file,
        audit_log_file=audit_log,
    )
    return _STATE


def refresh_runtime_state() -> RuntimeState:
    """Force recomputation of runtime state (used in tests when env changes)."""
    return build_runtime_state(force_refresh=True)


def get_directory(name: str) -> Path:
    """Convenience accessor for standard directories."""
    state = build_runtime_state()
    try:
        return state.directories[name]
    except KeyError as exc:
        raise KeyError(f"Unknown runtime directory '{name}'") from exc


def render_simulation_env(
    base_dir: Optional[Path] = None,
    *,
    secret_key: str = "test-secret-key",
    admin_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$G+a2uq+3hZbq90yZ/zsJkA$uVC0ZCQ0gcrnlEP4vqzQYCMEJTB64euXGsRuMXALuvs",
    database_name: str = "eu_tracker.db",
) -> Dict[str, str]:
    """
    Build a dictionary of environment variables that mirrors Render.

    Used by automated tests to spin up a clean environment without mutating the
    developer machine.
    """
    base_dir = base_dir or Path(tempfile.mkdtemp(prefix="complyeur_render_sim_")).resolve()
    persistent_dir = base_dir / "var" / "data"
    persistent_dir.mkdir(parents=True, exist_ok=True)
    return {
        "PERSISTENT_DIR": str(persistent_dir),
        "DATABASE_PATH": database_name,
        "SECRET_KEY": secret_key,
        "ADMIN_PASSWORD_HASH": admin_hash,
    }


def ensure_directories_exist(optional_dirs: Iterable[Path]) -> None:
    """Ensure arbitrary iterable of directories exists."""
    for directory in optional_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)

