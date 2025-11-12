from datetime import date, timedelta

import pytest

from app.models import get_db, init_db
from app.services import alerts as alerts_service


@pytest.fixture
def alert_app(app, monkeypatch):
    """Provide an application with a fresh in-memory database for alert tests."""
    with app.app_context():
        app.config['DATABASE'] = 'file:alerts_test?mode=memory&cache=shared'
        app.config['PERSISTENT_DB_CONN'] = None
        app.config['ADMIN_EMAIL'] = 'alerts@example.com'
        try:
            from flask import g
            if hasattr(g, '_db_conn'):
                try:
                    g._db_conn.close()
                finally:
                    delattr(g, '_db_conn')
        except Exception:
            pass
        init_db()
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    yield app


def _create_employee(conn, name='Compliance Tester'):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO employees (name) VALUES (?)', (name,))
    conn.commit()
    return cursor.lastrowid


def _create_trip(conn, employee_id, days_used):
    """Create a single Schengen trip ending yesterday spanning the given number of days."""
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_used - 1)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO trips (employee_id, country, entry_date, exit_date) VALUES (?, ?, ?, ?)',
        (employee_id, 'FR', start_date.isoformat(), end_date.isoformat()),
    )
    conn.commit()


def _fetch_alert_row(conn, alert_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,))
    return cursor.fetchone()


def test_check_alert_status_creates_alert(alert_app):
    with alert_app.app_context():
        conn = get_db()
        employee_id = _create_employee(conn, 'Yellow Threshold')
        _create_trip(conn, employee_id, 76)

        risk = alerts_service.check_alert_status(employee_id)
        assert risk == 'YELLOW'

        alerts = alerts_service.get_active_alerts()
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert['employee_id'] == employee_id
        assert alert['risk_level'] == 'YELLOW'
        assert alert['email_sent'] in (0, False)


def test_alert_escalation_updates_existing_record(alert_app):
    with alert_app.app_context():
        conn = get_db()
        employee_id = _create_employee(conn, 'Escalation Test')
        _create_trip(conn, employee_id, 80)

        alerts_service.check_alert_status(employee_id)
        initial_alert = alerts_service.get_active_alerts()[0]
        alert_id = initial_alert['id']

        # Mark emailed to confirm escalation resets the flag
        conn.execute('UPDATE alerts SET email_sent = 1 WHERE id = ?', (alert_id,))
        conn.commit()

        # Extend trip to trigger RED level
        conn.execute(
            'UPDATE trips SET exit_date = ? WHERE employee_id = ?',
            ((date.today() - timedelta(days=1)).isoformat(), employee_id),
        )
        conn.execute(
            'UPDATE trips SET entry_date = ? WHERE employee_id = ?',
            ((date.today() - timedelta(days=90)).isoformat(), employee_id),
        )
        conn.commit()

        risk = alerts_service.check_alert_status(employee_id)
        assert risk == 'RED'

        updated_alert = alerts_service.get_active_alerts()[0]
        assert updated_alert['id'] == alert_id
        assert updated_alert['risk_level'] == 'RED'
        assert updated_alert['email_sent'] in (0, False)


def test_resolve_alert_removes_from_active_list(alert_app):
    with alert_app.app_context():
        conn = get_db()
        employee_id = _create_employee(conn, 'Resolve Target')
        _create_trip(conn, employee_id, 85)

        alerts_service.check_alert_status(employee_id)
        alert = alerts_service.get_active_alerts()[0]

        assert alerts_service.resolve_alert(alert['id']) is True
        assert alerts_service.get_active_alerts() == []

        row = _fetch_alert_row(conn, alert['id'])
        assert row['resolved'] == 1


def test_send_pending_alert_emails_marks_flag(alert_app, monkeypatch):
    with alert_app.app_context():
        conn = get_db()
        employee_id = _create_employee(conn, 'Email Target')
        _create_trip(conn, employee_id, 90)

        alerts_service.check_alert_status(employee_id)
        alert = alerts_service.get_active_alerts()[0]

        monkeypatch.setattr(alerts_service, '_send_email', lambda *args, **kwargs: True)
        alert_app.config['ADMIN_EMAIL'] = 'compliance@example.com'

        sent = alerts_service.send_pending_alert_emails()
        assert sent == 1

        refreshed = alerts_service.get_active_alerts()[0]
        assert refreshed['email_sent'] == 1
