#!/usr/bin/env python3
"""
Utility script used by the Excel QA test suite to exercise the importer module
against controlled SQLite databases and emit JSON summaries that JavaScript
tests can assert on.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Excel importer for QA tests.")
    parser.add_argument("excel_path", help="Path to the Excel workbook to import.")
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to the SQLite database file that should be used for this run.",
    )
    parser.add_argument(
        "--imports",
        type=int,
        default=1,
        help="Number of times to invoke the importer against the same database.",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Retain the SQLite file after execution (useful for debugging).",
    )
    return parser.parse_args()


def ensure_clean_db(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)


def fetch_db_state(conn: sqlite3.Connection) -> Dict[str, Any]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM employees ORDER BY id")
    employees: List[Dict[str, Any]] = [
        {"id": row["id"], "name": row["name"]} for row in cur.fetchall()
    ]

    cur.execute(
        """
        SELECT t.id, e.name AS employee, t.country, t.entry_date, t.exit_date,
               t.travel_days
        FROM trips t
        JOIN employees e ON e.id = t.employee_id
        ORDER BY t.id
        """
    )
    trips: List[Dict[str, Any]] = [
        {
            "id": row["id"],
            "employee": row["employee"],
            "country": row["country"],
            "entry_date": row["entry_date"],
            "exit_date": row["exit_date"],
            "travel_days": row["travel_days"],
        }
        for row in cur.fetchall()
    ]
    return {"employees": employees, "trips": trips}


def main() -> int:
    args = parse_args()
    excel_path = Path(args.excel_path).resolve()
    db_path = Path(args.db_path).resolve()

    if not excel_path.exists():
        print(json.dumps({"success": False, "error": "Excel file not found"}))
        return 1

    ensure_clean_db(db_path)

    # Route the Flask application to our isolated database.
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ.setdefault("FLASK_DEBUG", "false")

    # Creating the app initialises the database via init_db().
    from app import create_app
    from app.models import get_db
    from importer import import_excel

    app = create_app()

    summaries: List[Dict[str, Any]] = []
    with app.app_context():
        conn = get_db()
        for _ in range(max(1, args.imports)):
            result = import_excel(str(excel_path), db_conn=conn)
            summaries.append(result)

        db_state = fetch_db_state(conn)

    output = {
        "success": True,
        "imports": summaries,
        "db": db_state,
    }

    print(json.dumps(output, default=str))

    if not args.keep_db:
        try:
            os.unlink(db_path)
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
