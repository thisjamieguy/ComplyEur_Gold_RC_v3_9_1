import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app


@pytest.fixture(scope="session")
def app():
    """Provide application instance for pytest-flask fixtures (legacy tests)."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def phase38_app(tmp_path, monkeypatch):
    """Create an isolated Flask app backed by the Phase 3.8 fixture database."""
    fixture_db = Path(__file__).parent / "fixtures" / "test_data.db"
    db_copy = tmp_path / "phase38.db"
    shutil.copy(fixture_db, db_copy)

    monkeypatch.setenv("DATABASE_PATH", str(db_copy))
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_copy}")
    monkeypatch.setenv("AUTH_TOTP_ENABLED", "false")
    monkeypatch.setenv("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD", "admin123"))

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


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for testing."""
    import tempfile
    fd, path = tempfile.mkstemp(prefix="complyeur_test_", suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def test_app(test_db_path, monkeypatch):
    """Create Flask app with test database."""
    monkeypatch.setenv("DATABASE_PATH", test_db_path)
    monkeypatch.setenv("DB_PATH", test_db_path)
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("APP_VERSION", "test-1.0.0")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        DB_PATH=test_db_path,
        DATABASE=test_db_path,
        SECRET_KEY="test-secret",
        APP_VERSION="test-1.0.0",
        WTF_CSRF_ENABLED=False,
    )
    
    # Ensure we have a basic admin user for testing
    with flask_app.app_context():
        # Try to create admin user via legacy admin table
        try:
            import sqlite3
            conn = sqlite3.connect(test_db_path)
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
