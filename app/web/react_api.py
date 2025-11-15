"""React frontend API endpoints."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from flask import current_app, jsonify, request

from app.middleware.auth import login_required
from .base import main_bp


@main_bp.route('/api/trips', methods=['GET'])
@login_required
def api_trips_get():
    """Get all trips and employees for React frontend."""
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = [dict(row) for row in c.fetchall()]

        c.execute(
            '''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date,
                       t.is_private, t.job_ref, t.ghosted, t.travel_days, t.purpose,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                ORDER BY t.entry_date
            '''
        )
        trips = [dict(row) for row in c.fetchall()]

        return jsonify({'employees': employees, 'trips': trips, 'generated_at': datetime.now().isoformat()})
    finally:
        conn.close()


@main_bp.route('/api/trips', methods=['POST'])
@login_required
def api_trips_post():
    """Create a new trip."""
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        data = request.get_json()

        required_fields = ['employee_id', 'country', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        c.execute(
            '''
                INSERT INTO trips (employee_id, country, entry_date, exit_date,
                                   is_private, job_ref, ghosted, travel_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                data['employee_id'],
                data['country'],
                data['start_date'],
                data['end_date'],
                data.get('is_private', False),
                data.get('job_ref', ''),
                data.get('ghosted', False),
                data.get('travel_days', 0),
            ),
        )

        trip_id = c.lastrowid
        conn.commit()

        c.execute(
            '''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date,
                       t.is_private, t.job_ref, t.ghosted, t.travel_days,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                WHERE t.id = ?
            ''',
            (trip_id,),
        )

        trip = dict(c.fetchone())
        return jsonify(trip), 201

    except Exception as exc:  # pragma: no cover - defensive
        conn.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        conn.close()


@main_bp.route('/api/trips/<int:trip_id>', methods=['PATCH'])
@login_required
def api_trips_patch(trip_id: int):
    """Update an existing trip."""
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        data = request.get_json()

        update_fields = []
        update_values = []
        allowed_fields = [
            'employee_id',
            'country',
            'start_date',
            'end_date',
            'is_private',
            'job_ref',
            'ghosted',
            'travel_days',
        ]

        for field in allowed_fields:
            if field in data:
                if field in ['start_date', 'end_date']:
                    db_field = 'entry_date' if field == 'start_date' else 'exit_date'
                    update_fields.append(f'{db_field} = ?')
                    update_values.append(data[field])
                else:
                    update_fields.append(f'{field} = ?')
                    update_values.append(data[field])

        if not update_fields:
            return jsonify({'error': 'No valid fields provided for update'}), 400

        update_values.append(trip_id)

        c.execute(f"UPDATE trips SET {', '.join(update_fields)} WHERE id = ?", update_values)
        conn.commit()

        c.execute(
            '''
                SELECT t.id, t.employee_id, t.country, t.entry_date, t.exit_date,
                       t.is_private, t.job_ref, t.ghosted, t.travel_days,
                       e.name as employee_name
                FROM trips t
                JOIN employees e ON t.employee_id = e.id
                WHERE t.id = ?
            ''',
            (trip_id,),
        )

        trip = dict(c.fetchone())
        return jsonify(trip)

    except Exception as exc:  # pragma: no cover - defensive
        conn.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        conn.close()
