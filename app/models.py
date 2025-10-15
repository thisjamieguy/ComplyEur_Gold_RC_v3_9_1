import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

def get_db():
    """Get database connection"""
    from flask import current_app
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Create admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

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
                 exit_date: str, purpose: Optional[str] = None, created_at: Optional[str] = None):
        self.id = id
        self.employee_id = employee_id
        self.country = country
        self.entry_date = entry_date
        self.exit_date = exit_date
        self.purpose = purpose
        self.created_at = created_at
    
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
               exit_date: str, purpose: Optional[str] = None) -> 'Trip':
        """Create new trip"""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO trips (employee_id, country, entry_date, exit_date, purpose)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, country, entry_date, exit_date, purpose))
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
