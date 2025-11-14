import sqlite3

TEST_ADMIN_HASH = "$argon2id$v=19$m=65536,t=3,p=4$G+a2uq+3hZbq90yZ/zsJkA$uVC0ZCQ0gcrnlEP4vqzQYCMEJTB64euXGsRuMXALuvs"


def test_schema_auto_created(fresh_app):
    app, db_path = fresh_app
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    tables = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"employees", "trips", "admin"}.issubset(tables)


def test_admin_hash_synced_from_env(fresh_app):
    app, db_path = fresh_app
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admin WHERE id = 1")
    row = c.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == TEST_ADMIN_HASH

