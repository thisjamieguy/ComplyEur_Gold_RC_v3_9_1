import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.runtime_env import refresh_runtime_state

TEST_SECRET_KEY = "test-secret-key"
TEST_ADMIN_HASH = "$argon2id$v=19$m=65536,t=3,p=4$G+a2uq+3hZbq90yZ/zsJkA$uVC0ZCQ0gcrnlEP4vqzQYCMEJTB64euXGsRuMXALuvs"


def _configure_runtime_env(monkeypatch, persistent_dir: Path, database_path: Path) -> None:
    persistent_dir.mkdir(parents=True, exist_ok=True)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PERSISTENT_DIR", str(persistent_dir))
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_ADMIN_HASH)
    refresh_runtime_state()
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{database_path}")


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """Provide application instance for pytest-flask fixtures (legacy tests)."""
    base_dir = Path(tmp_path_factory.mktemp("session_env"))
    persistent_dir = base_dir / "var" / "data"
    db_path = persistent_dir / "session_app.db"
    persistent_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    previous = {var: os.environ.get(var) for var in ("PERSISTENT_DIR", "DATABASE_PATH", "SECRET_KEY", "ADMIN_PASSWORD_HASH")}
    os.environ["PERSISTENT_DIR"] = str(persistent_dir)
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["ADMIN_PASSWORD_HASH"] = TEST_ADMIN_HASH
    refresh_runtime_state()
    os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app

    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    os.environ.pop("SQLALCHEMY_DATABASE_URI", None)


@pytest.fixture
def phase38_app(tmp_path, monkeypatch):
    """Create an isolated Flask app backed by the Phase 3.8 fixture database."""
    fixture_db = Path(__file__).parent / "fixtures" / "test_data.db"
    persistent_dir = tmp_path / "var" / "data"
    db_copy = persistent_dir / "phase38.db"
    shutil.copy(fixture_db, db_copy)

    _configure_runtime_env(monkeypatch, persistent_dir, db_copy)
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_copy}")
    monkeypatch.setenv("AUTH_TOTP_ENABLED", "false")

    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def phase38_client(phase38_app):
    """Test client bound to the isolated Phase 3.8 Flask app."""
    return phase38_app.test_client()


@pytest.fixture
def test_app(tmp_path, monkeypatch):
    """Create Flask app with test database."""
    persistent_dir = tmp_path / "var" / "data"
    db_path = persistent_dir / "test_app.db"
    _configure_runtime_env(monkeypatch, persistent_dir, db_path)
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("APP_VERSION", "test-1.0.0")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        DB_PATH=str(db_path),
        DATABASE=str(db_path),
        SECRET_KEY=TEST_SECRET_KEY,
        APP_VERSION="test-1.0.0",
        WTF_CSRF_ENABLED=False,
    )
    
    # Ensure we have a basic admin user for testing
    with flask_app.app_context():
        # Try to create admin user via legacy admin table
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, password_hash TEXT)")
            # Check if admin exists
            cur.execute("SELECT COUNT(*) FROM admin WHERE id = 1")
            if cur.fetchone()[0] == 0:
                # Create admin with default password hash (admin123)
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash("admin123")
                cur.execute("INSERT INTO admin(id, password_hash) VALUES (1, ?)", (password_hash,))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Fallback if admin table creation fails
    
    return flask_app


@pytest.fixture
def client(test_app):
    """Test client for unauthenticated requests."""
    return test_app.test_client()


@pytest.fixture
def auth_client(client):
    """Test client with authenticated session (admin/admin123)."""
    # Bootstrap session by posting to /login
    resp = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    # Should redirect on success (302) or return 200 if already on dashboard
    assert resp.status_code in (302, 200), f"Login failed with status {resp.status_code}"
    return client


@pytest.fixture
def runtime_env(tmp_path, monkeypatch):
    """Provide a normalised runtime environment for tests needing direct DB access."""
    persistent_dir = tmp_path / "var" / "data"
    db_path = persistent_dir / "runtime_env.db"
    _configure_runtime_env(monkeypatch, persistent_dir, db_path)
    return {
        "persistent_dir": persistent_dir,
        "database_path": db_path,
    }


@pytest.fixture
def fresh_app(tmp_path, monkeypatch):
    """Return a brand-new app instance and associated database path."""
    persistent_dir = tmp_path / "var" / "data"
    db_path = persistent_dir / "fresh_app.db"
    _configure_runtime_env(monkeypatch, persistent_dir, db_path)
    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return flask_app, db_path
