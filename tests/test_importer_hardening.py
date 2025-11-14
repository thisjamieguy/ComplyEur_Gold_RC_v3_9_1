from pathlib import Path
import sqlite3

import pytest

from importer import get_database_path, import_excel
from app.runtime_env import refresh_runtime_state

TEST_ADMIN_HASH = "$argon2id$v=19$m=65536,t=3,p=4$G+a2uq+3hZbq90yZ/zsJkA$uVC0ZCQ0gcrnlEP4vqzQYCMEJTB64euXGsRuMXALuvs"
SAMPLE_DIR = Path(__file__).parent / "sample_files"


def _init_basic_schema(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            country TEXT NOT NULL,
            entry_date DATE NOT NULL,
            exit_date DATE NOT NULL,
            purpose TEXT,
            job_ref TEXT,
            ghosted BOOLEAN DEFAULT 0,
            travel_days INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def test_get_database_path_relative(runtime_env):
    db_path = Path(get_database_path())
    assert db_path == runtime_env["database_path"]


def test_get_database_path_absolute(tmp_path, monkeypatch):
    persistent_dir = tmp_path / "var" / "data"
    absolute_db = tmp_path / "custom" / "absolute.db"
    persistent_dir.mkdir(parents=True, exist_ok=True)
    absolute_db.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PERSISTENT_DIR", str(persistent_dir))
    monkeypatch.setenv("DATABASE_PATH", str(absolute_db))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_ADMIN_HASH)

    path = Path(get_database_path(force_refresh=True))
    assert path == absolute_db.resolve()


def test_import_excel_success(runtime_env):
    db_path = runtime_env["database_path"]
    _init_basic_schema(db_path)

    sample_file = SAMPLE_DIR / "basic_valid.xlsx"
    result = import_excel(str(sample_file), enable_extended_scan=True)

    assert result["success"] is True
    assert result["trips_added"] > 0

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM trips")
    row_count = c.fetchone()[0]
    conn.close()
    assert row_count == result["trips_added"]


@pytest.mark.parametrize(
    "filename,expected_error",
    [
        ("invalid_missing_dates.xlsx", "date header row"),
        ("corrupted.xlsx", "Unable to open Excel file"),
    ],
)
def test_import_excel_validation_failures(runtime_env, filename, expected_error):
    db_path = runtime_env["database_path"]
    _init_basic_schema(db_path)

    sample_file = SAMPLE_DIR / filename
    result = import_excel(str(sample_file), enable_extended_scan=True)

    assert result["success"] is False
    assert expected_error in result["error"]

