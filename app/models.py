import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from flask import g


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply performance-related PRAGMAs for local SQLite.

    Safe for local-only ComplyEur usage; improves write performance and concurrency.
    """
    try:
        # Integrity and foreign keys
        conn.execute('PRAGMA foreign_keys = ON')
        # WAL improves concurrent reads; normal sync balances durability and speed
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA synchronous = NORMAL')
        # Increase cache and prefer memory for temp objects
        conn.execute('PRAGMA cache_size = -20000')  # ~20MB
        conn.execute('PRAGMA temp_store = MEMORY')
        # Enable mmap for faster I/O when supported (~128MB)
        conn.execute('PRAGMA mmap_size = 134217728')
    except Exception:
        # Best-effort: ignore if any pragma is unsupported
        pass

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
            _apply_pragmas(persistent)
            current_app.config['PERSISTENT_DB_CONN'] = persistent
        return persistent

    # Use a single connection per request context for file-based DBs
    conn = getattr(g, '_db_conn', None)
    if conn is None:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _apply_pragmas(conn)
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
            job_ref TEXT,
            ghosted BOOLEAN DEFAULT 0,
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

    # Add job_ref column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE trips ADD COLUMN job_ref TEXT')
    except sqlite3.OperationalError:
        # Column already exists, ignore error
        pass

    # Add ghosted column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE trips ADD COLUMN ghosted BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        # Column already exists, ignore error
        pass
    
    # Create alerts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved INTEGER DEFAULT 0,
            email_sent INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alerts_employee_active ON alerts (employee_id, resolved)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts (created_at)')
    
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
    
    # Create news_sources table
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            license_note TEXT
        )
    ''')
    
    # Create news_cache table
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            title TEXT NOT NULL,
            url TEXT UNIQUE,
            published_at DATETIME,
            summary TEXT,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES news_sources (id)
        )
    ''')
    
    # Seed news_sources if empty
    c.execute('SELECT COUNT(*) FROM news_sources')
    if c.fetchone()[0] == 0:
        # EU Commission and Home Affairs feeds (enabled by default)
        eu_sources = [
            ('EU Home Affairs', 'https://home-affairs.ec.europa.eu/news/rss_en.xml', 1, None),
            ('European Commission News', 'https://ec.europa.eu/news/rss_en.xml', 1, None),
        ]
        
        # Per-country GOV.UK travel advice feeds (enabled by default)
        country_sources = [
            ('Austria Travel Advice', 'https://www.gov.uk/foreign-travel-advice/austria', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Belgium Travel Advice', 'https://www.gov.uk/foreign-travel-advice/belgium', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Bulgaria Travel Advice', 'https://www.gov.uk/foreign-travel-advice/bulgaria', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Croatia Travel Advice', 'https://www.gov.uk/foreign-travel-advice/croatia', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Cyprus Travel Advice', 'https://www.gov.uk/foreign-travel-advice/cyprus', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Czech Republic Travel Advice', 'https://www.gov.uk/foreign-travel-advice/czech-republic', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Denmark Travel Advice', 'https://www.gov.uk/foreign-travel-advice/denmark', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Estonia Travel Advice', 'https://www.gov.uk/foreign-travel-advice/estonia', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Finland Travel Advice', 'https://www.gov.uk/foreign-travel-advice/finland', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('France Travel Advice', 'https://www.gov.uk/foreign-travel-advice/france', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Germany Travel Advice', 'https://www.gov.uk/foreign-travel-advice/germany', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Greece Travel Advice', 'https://www.gov.uk/foreign-travel-advice/greece', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Hungary Travel Advice', 'https://www.gov.uk/foreign-travel-advice/hungary', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Ireland Travel Advice', 'https://www.gov.uk/foreign-travel-advice/ireland', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Italy Travel Advice', 'https://www.gov.uk/foreign-travel-advice/italy', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Latvia Travel Advice', 'https://www.gov.uk/foreign-travel-advice/latvia', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Lithuania Travel Advice', 'https://www.gov.uk/foreign-travel-advice/lithuania', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Luxembourg Travel Advice', 'https://www.gov.uk/foreign-travel-advice/luxembourg', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Malta Travel Advice', 'https://www.gov.uk/foreign-travel-advice/malta', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Netherlands Travel Advice', 'https://www.gov.uk/foreign-travel-advice/netherlands', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Poland Travel Advice', 'https://www.gov.uk/foreign-travel-advice/poland', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Portugal Travel Advice', 'https://www.gov.uk/foreign-travel-advice/portugal', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Romania Travel Advice', 'https://www.gov.uk/foreign-travel-advice/romania', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Slovakia Travel Advice', 'https://www.gov.uk/foreign-travel-advice/slovakia', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Slovenia Travel Advice', 'https://www.gov.uk/foreign-travel-advice/slovenia', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Spain Travel Advice', 'https://www.gov.uk/foreign-travel-advice/spain', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Sweden Travel Advice', 'https://www.gov.uk/foreign-travel-advice/sweden', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Iceland Travel Advice', 'https://www.gov.uk/foreign-travel-advice/iceland', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Norway Travel Advice', 'https://www.gov.uk/foreign-travel-advice/norway', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Switzerland Travel Advice', 'https://www.gov.uk/foreign-travel-advice/switzerland', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('Liechtenstein Travel Advice', 'https://www.gov.uk/foreign-travel-advice/liechtenstein', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
        ]
        
        # Generic global feed (disabled by default)
        global_sources = [
            ('GOV.UK Foreign Travel', 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom', 0, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
            ('SchengenVisaInfo', 'https://www.schengenvisainfo.com/feed/', 0, None)
        ]
        
        # Insert all sources
        all_sources = eu_sources + country_sources + global_sources
        c.executemany('INSERT INTO news_sources (name, url, enabled, license_note) VALUES (?, ?, ?, ?)', all_sources)
    
    # Create indexes for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_employee_id ON trips(employee_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_entry_date ON trips(entry_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_exit_date ON trips(exit_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(entry_date, exit_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_news_cache_source ON news_cache(source_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_news_cache_fetched ON news_cache(fetched_at)')
    
    # Performance optimization indexes (Phase 1)
    # Composite index for dashboard queries (employee_id + dates)
    c.execute('CREATE INDEX IF NOT EXISTS idx_trips_employee_dates ON trips(employee_id, entry_date, exit_date)')
    # Index for employee name sorting
    c.execute('CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name COLLATE NOCASE)')

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
        # OPTIMIZATION: Select specific columns instead of SELECT *
        c.execute('SELECT id, name, created_at FROM employees ORDER BY name')
        employees = [Employee(**dict(row)) for row in c.fetchall()]
        # Connection managed by Flask teardown handler
        return employees
    
    @classmethod
    def get_by_id(cls, employee_id: int) -> Optional['Employee']:
        """Get employee by ID"""
        conn = get_db()
        c = conn.cursor()
        # OPTIMIZATION: Select specific columns instead of SELECT *
        c.execute('SELECT id, name, created_at FROM employees WHERE id = ?', (employee_id,))
        row = c.fetchone()
        # Connection managed by Flask teardown handler
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
    def __init__(
        self,
        id: int,
        employee_id: int,
        country: str,
        entry_date: str,
        exit_date: str,
        purpose: Optional[str] = None,
        travel_days: Optional[int] = 0,
        created_at: Optional[str] = None,
        is_private: bool = False,
        job_ref: Optional[str] = None,
        ghosted: Optional[int] = 0,
        **extra,
    ):
        self.id = id
        self.employee_id = employee_id
        self.country = country
        self.entry_date = entry_date
        self.exit_date = exit_date
        self.purpose = purpose
        self.travel_days = travel_days or 0
        self.created_at = created_at
        self.is_private = bool(is_private)
        self.job_ref = job_ref
        self.ghosted = bool(ghosted)
        # Preserve any additional payload for forward compatibility
        self._extra = extra

    @property
    def start_date(self) -> str:
        return self.entry_date

    @property
    def end_date(self) -> str:
        return self.exit_date

    def to_dict(self, employee_name: Optional[str] = None) -> Dict[str, Any]:
        """Serialize trip for API responses."""
        start = self.start_date
        end = self.end_date
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee": employee_name,
            "country": self.country,
            "job_ref": self.job_ref,
            "start_date": start if isinstance(start, str) else start.isoformat(),
            "end_date": end if isinstance(end, str) else end.isoformat(),
            "ghosted": bool(self.ghosted),
            "is_private": bool(self.is_private),
            "purpose": self.purpose,
        }
    
    @classmethod
    def get_by_employee(cls, employee_id: int) -> List['Trip']:
        """Get all trips for an employee"""
        conn = get_db()
        c = conn.cursor()
        # OPTIMIZATION: Select specific columns instead of SELECT *
        c.execute('''
            SELECT id, employee_id, country, entry_date, exit_date, purpose, 
                   travel_days, is_private, job_ref, ghosted, created_at 
            FROM trips 
            WHERE employee_id = ? 
            ORDER BY entry_date DESC
        ''', (employee_id,))
        trips = [Trip(**dict(row)) for row in c.fetchall()]
        # Connection managed by Flask teardown handler
        return trips
    
    @classmethod
    def get_by_id(cls, trip_id: int) -> Optional['Trip']:
        """Get trip by ID"""
        conn = get_db()
        c = conn.cursor()
        # OPTIMIZATION: Select specific columns instead of SELECT *
        c.execute('''
            SELECT id, employee_id, country, entry_date, exit_date, purpose, 
                   travel_days, is_private, job_ref, ghosted, created_at 
            FROM trips 
            WHERE id = ?
        ''', (trip_id,))
        row = c.fetchone()
        # Connection managed by Flask teardown handler
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
