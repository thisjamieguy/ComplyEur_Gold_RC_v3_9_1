import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from flask import g

def get_db():
    """Get database connection (shared for request context).
    Supports in-memory DB in tests using a shared cache.
    """
    from flask import current_app
    db_path = current_app.config['DATABASE']

    # If using shared in-memory DB, keep a persistent process-wide connection alive
    if db_path == ':memory:' or (isinstance(db_path, str) and db_path.startswith('file:eu_memdb')):
        if db_path == ':memory:':
            db_path = 'file:eu_memdb?mode=memory&cache=shared'
            current_app.config['DATABASE'] = db_path
        persistent = current_app.config.get('PERSISTENT_DB_CONN')
        def ensure_open(conn):
            try:
                conn.execute('SELECT 1')
                return conn
            except Exception:
                return None

        if persistent is None or ensure_open(persistent) is None:
            persistent = sqlite3.connect(db_path, uri=True, check_same_thread=False)
            persistent.row_factory = sqlite3.Row
            try:
                persistent.execute('PRAGMA foreign_keys = ON')
            except Exception:
                pass
            current_app.config['PERSISTENT_DB_CONN'] = persistent
        return persistent

    # Use a single connection per request context for file-based DBs
    conn = getattr(g, '_db_conn', None)
    if conn is None:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA foreign_keys = ON')
        except Exception:
            pass
        g._db_conn = conn
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    c = conn.cursor()
    
    # Create employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create trips table
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            country TEXT NOT NULL,
            entry_date DATE NOT NULL,
            exit_date DATE NOT NULL,
            purpose TEXT,
            travel_days INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Add travel_days column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE trips ADD COLUMN travel_days INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        # Column already exists, ignore error
        pass
    
    # Add is_private column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE trips ADD COLUMN is_private BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        # Column already exists, ignore error
        pass
    
    # Create admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            password_hash TEXT NOT NULL,
            company_name TEXT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add new columns to existing admin table if they don't exist
    try:
        c.execute('ALTER TABLE admin ADD COLUMN company_name TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute('ALTER TABLE admin ADD COLUMN full_name TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute('ALTER TABLE admin ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute('ALTER TABLE admin ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Create indexes for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_employee_id ON trips(employee_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_entry_date ON trips(entry_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_exit_date ON trips(exit_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(entry_date, exit_date)')

    # Ensure default admin exists (used by tests and first-run local dev)
    try:
        c.execute('SELECT COUNT(1) FROM admin WHERE id = 1')
        row = c.fetchone()
        if not row or row[0] == 0:
            try:
                # Hash default password 'admin123'
                from .services.hashing import Hasher
                hasher = Hasher()
                default_hash = hasher.hash('admin123')
            except Exception:
                # Fallback: store as-is (tests rely on Hasher normally)
                default_hash = 'admin123'
            c.execute('INSERT INTO admin (id, password_hash) VALUES (1, ?)', (default_hash,))
    except Exception:
        pass
    
    conn.commit()
    # Do not close persistent in-memory connection; keep schema alive for tests
    from flask import current_app
    db_path = current_app.config.get('DATABASE', '')
    if not (isinstance(db_path, str) and db_path.startswith('file:eu_memdb')):
        try:
            conn.close()
        except Exception:
            pass

class Employee:
    def __init__(self, id: int, name: str, created_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.created_at = created_at
    
    @classmethod
    def get_all(cls) -> List['Employee']:
        """Get all employees"""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM employees ORDER BY name')
        employees = [Employee(**dict(row)) for row in c.fetchall()]
        conn.close()
        return employees
    
    @classmethod
    def get_by_id(cls, employee_id: int) -> Optional['Employee']:
        """Get employee by ID"""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        row = c.fetchone()
        conn.close()
        return Employee(**dict(row)) if row else None
    
    @classmethod
    def create(cls, name: str) -> 'Employee':
        """Create new employee"""
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO employees (name) VALUES (?)', (name,))
        employee_id = c.lastrowid
        conn.commit()
        conn.close()
        return cls.get_by_id(employee_id)
    
    def delete(self):
        """Delete employee and all associated trips"""
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM trips WHERE employee_id = ?', (self.id,))
        c.execute('DELETE FROM employees WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()

class Trip:
    def __init__(self, id: int, employee_id: int, country: str, entry_date: str, 
                 exit_date: str, purpose: Optional[str] = None, created_at: Optional[str] = None, 
                 is_private: bool = False):
        self.id = id
        self.employee_id = employee_id
        self.country = country
        self.entry_date = entry_date
        self.exit_date = exit_date
        self.purpose = purpose
        self.created_at = created_at
        self.is_private = is_private
    
    @classmethod
    def get_by_employee(cls, employee_id: int) -> List['Trip']:
        """Get all trips for an employee"""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM trips WHERE employee_id = ? ORDER BY entry_date DESC', (employee_id,))
        trips = [Trip(**dict(row)) for row in c.fetchall()]
        conn.close()
        return trips
    
    @classmethod
    def get_by_id(cls, trip_id: int) -> Optional['Trip']:
        """Get trip by ID"""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
        row = c.fetchone()
        conn.close()
        return Trip(**dict(row)) if row else None
    
    @classmethod
    def create(cls, employee_id: int, country: str, entry_date: str, 
               exit_date: str, purpose: Optional[str] = None, is_private: bool = False) -> 'Trip':
        """Create new trip"""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, purpose, is_private)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, country, entry_date, exit_date, purpose, is_private))
        trip_id = c.lastrowid
        conn.commit()
        conn.close()
        return cls.get_by_id(trip_id)
    
    def delete(self):
        """Delete trip"""
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM trips WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()

class Admin:
    @classmethod
    def get_password_hash(cls) -> Optional[str]:
        """Get admin password hash"""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT password_hash FROM admin WHERE id = 1')
        row = c.fetchone()
        conn.close()
        return row['password_hash'] if row else None
    
    @classmethod
    def set_password_hash(cls, password_hash: str):
        """Set admin password hash"""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO admin (id, password_hash)
            VALUES (1, ?)
        ''', (password_hash,))
        conn.commit()
        conn.close()
    
    @classmethod
    def exists(cls) -> bool:
        """Check if admin exists"""
        return cls.get_password_hash() is not None
