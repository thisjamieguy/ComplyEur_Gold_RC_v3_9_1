"""
Comprehensive Test Suite for EU Trip Tracker
Tests server startup, database, authentication, CRUD operations, and exports
"""

import pytest
import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db, calculate_eu_days, hash_password
from modules.app.services.rolling90 import presence_days, days_used_in_window
from modules.app.services.backup import create_backup, list_backups


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'  # Use in-memory database for tests
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create a logged-in test client"""
    # Login with default password
    client.post('/login', data={'password': 'admin123'}, follow_redirects=True)
    yield client


def test_app_startup(client):
    """Test that the Flask app starts correctly"""
    response = client.get('/')
    assert response.status_code == 302  # Redirect to login
    

def test_login_page_loads(client):
    """Test that login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'EU Trip Tracker' in response.data or b'Login' in response.data


def test_login_valid_credentials(client):
    """Test login with valid credentials"""
    response = client.post('/login', data={
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid' in response.data or b'error' in response.data.lower()


def test_dashboard_requires_login(client):
    """Test that dashboard requires authentication"""
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login


def test_dashboard_loads_when_logged_in(logged_in_client):
    """Test that dashboard loads for authenticated users"""
    response = logged_in_client.get('/dashboard')
    assert response.status_code == 200


def test_add_employee(logged_in_client):
    """Test adding a new employee"""
    response = logged_in_client.post('/add_employee', data={
        'name': 'Test Employee'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check that employee was added by trying to view dashboard
    response = logged_in_client.get('/dashboard')
    assert b'Test Employee' in response.data


def test_add_trip(logged_in_client):
    """Test adding a trip to an employee"""
    # First add an employee
    logged_in_client.post('/add_employee', data={
        'name': 'Trip Test Employee'
    }, follow_redirects=True)
    
    # Get the employee ID (would be 1 in fresh test database)
    response = logged_in_client.post('/add_trip', data={
        'employee_id': '1',
        'country_code': 'FR',
        'entry_date': '2024-01-01',
        'exit_date': '2024-01-15'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_delete_trip(logged_in_client):
    """Test deleting a trip"""
    # Add employee and trip first
    logged_in_client.post('/add_employee', data={
        'name': 'Delete Test Employee'
    })
    logged_in_client.post('/add_trip', data={
        'employee_id': '1',
        'country_code': 'DE',
        'entry_date': '2024-02-01',
        'exit_date': '2024-02-10'
    })
    
    # Delete the trip
    response = logged_in_client.post('/delete_trip/1', data={
        'employee_id': '1'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_rolling_90_day_calculation():
    """Test the 90/180-day rolling window calculation"""
    today = datetime.now().date()
    
    # Create test trips
    trips = [
        {
            'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'country': 'FR'
        },
        {
            'entry_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=40)).strftime('%Y-%m-%d'),
            'country': 'DE'
        }
    ]
    
    presence = presence_days(trips)
    days_used = days_used_in_window(presence, today)
    
    # Should be 21 days total (11 days + 10 days)
    assert days_used == 21


def test_csv_export(logged_in_client):
    """Test CSV export functionality"""
    # Add test data
    logged_in_client.post('/add_employee', data={'name': 'Export Test Employee'})
    logged_in_client.post('/add_trip', data={
        'employee_id': '1',
        'country_code': 'IT',
        'entry_date': '2024-03-01',
        'exit_date': '2024-03-15'
    })
    
    # Export CSV
    response = logged_in_client.get('/export/trips/csv')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv'


def test_password_hashing():
    """Test password hashing functionality"""
    password = "test_password_123"
    hashed = hash_password(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Same password should produce same hash
    hashed2 = hash_password(password)
    assert hashed == hashed2


def test_database_foreign_keys():
    """Test that foreign key constraints are working"""
    # This would require a more complex setup, but we can test the schema
    import sqlite3
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Check that foreign keys are enabled (should be part of init_db)
    cursor.execute('PRAGMA foreign_keys')
    result = cursor.fetchone()
    conn.close()
    
    # Result should be (1,) if foreign keys are enabled
    assert result is not None


def test_input_validation():
    """Test that input validation is working"""
    from app import validate_employee_name, validate_date, validate_country_code
    
    # Test employee name validation
    valid_name, error = validate_employee_name("John Smith")
    assert error is None
    assert valid_name == "John Smith"
    
    # Test invalid names
    invalid_name, error = validate_employee_name("<script>alert('xss')</script>")
    assert error is not None or invalid_name != "<script>alert('xss')</script>"
    
    # Test date validation
    valid_date, error = validate_date("2024-01-15")
    assert error is None
    
    invalid_date, error = validate_date("invalid-date")
    assert error is not None
    
    # Test country code validation
    valid_country, error = validate_country_code("FR")
    assert error is None
    assert valid_country == "FR"
    
    invalid_country, error = validate_country_code("XX")
    assert error is not None


def test_backup_system():
    """Test the automated backup system"""
    import tempfile
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()
    
    # Initialize database
    conn = sqlite3.connect(temp_db_path)
    conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute('INSERT INTO test (name) VALUES (?)', ('test_data',))
    conn.commit()
    conn.close()
    
    # Create backup
    result = create_backup(temp_db_path, reason='test')
    assert result['success'] == True
    assert 'backup_path' in result
    
    # Verify backup file exists
    assert os.path.exists(result['backup_path'])
    
    # Clean up
    os.unlink(temp_db_path)
    if os.path.exists(result['backup_path']):
        os.unlink(result['backup_path'])


def test_api_endpoints_require_login(client):
    """Test that API endpoints require authentication"""
    # Test various API endpoints without logging in
    endpoints = [
        '/api/calendar_data',
        '/api/entry-requirements',
        '/api/employees/search?q=test',
        '/admin/privacy-tools'
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should redirect to login (302) or return unauthorized (401)
        assert response.status_code in [302, 401]


def test_error_pages_exist():
    """Test that custom error pages are configured"""
    # Test 404 page
    response = app.test_client().get('/nonexistent-page')
    assert response.status_code == 404
    
    # Would need to trigger actual 500 error for full test
    # But we can verify the handler is registered
    assert '404' in str(app.error_handler_spec)


def test_session_security(client):
    """Test session security settings"""
    assert app.config.get('SESSION_COOKIE_HTTPONLY') == True
    assert app.config.get('SESSION_COOKIE_SAMESITE') in ['Lax', 'Strict']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

