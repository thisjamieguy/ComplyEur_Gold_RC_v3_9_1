"""Seed script to create test data (one employee + trip) for manual testing."""

import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH") or os.environ.get("DATABASE_PATH", "data/complyeur.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
cur.execute("""CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    country TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
)""")

cur.execute("INSERT INTO employees(name) VALUES ('Seed User')")
eid = cur.lastrowid

cur.execute("INSERT INTO trips(employee_id, country, start_date, end_date) VALUES (?,?,?,?)",
            (eid, "DE", "2025-02-01", "2025-02-10"))

con.commit()
con.close()

print("Seeded: employee 'Seed User' with one trip.")
