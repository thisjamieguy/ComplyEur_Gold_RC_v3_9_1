from pathlib import Path

import pytest

from app.runtime_env import (
    REQUIRED_ENV_VARS,
    build_runtime_state,
    refresh_runtime_state,
    render_simulation_env,
)

TEST_ADMIN_HASH = "$argon2id$v=19$m=65536,t=3,p=4$G+a2uq+3hZbq90yZ/zsJkA$uVC0ZCQ0gcrnlEP4vqzQYCMEJTB64euXGsRuMXALuvs"


def test_runtime_state_normalises_relative_db_path(tmp_path, monkeypatch):
    persistent_dir = tmp_path / "var" / "data"
    db_relative = "data/eu_tracker.db"
    monkeypatch.setenv("PERSISTENT_DIR", str(persistent_dir))
    monkeypatch.setenv("DATABASE_PATH", db_relative)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_ADMIN_HASH)

    state = refresh_runtime_state()

    expected_db_path = (persistent_dir / db_relative).resolve()
    assert state.database_path == expected_db_path
    for dirname in ("uploads", "logs", "exports", "backups"):
        assert (persistent_dir / dirname).exists()


def test_missing_env_vars_fail_fast(monkeypatch):
    for var in REQUIRED_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError):
        refresh_runtime_state()


def test_render_simulation_env_creates_structure(tmp_path):
    env_map = render_simulation_env(base_dir=tmp_path, database_name="sim/test.db")
    persistent_dir = Path(env_map["PERSISTENT_DIR"])
    assert persistent_dir.exists()
    assert Path(env_map["DATABASE_PATH"]).name == "test.db" or Path(env_map["DATABASE_PATH"]).suffix == ".db"

