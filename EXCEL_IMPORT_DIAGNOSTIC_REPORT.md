# Excel Import 500 Error - Diagnostic Report

## Issue Summary

The Excel import functionality is failing with a 500 Internal Server Error due to database connection conflicts and improper error response handling. The `importer.py` module creates its own SQLite connection that conflicts with Flask's connection management system, and error responses are not properly formatted for Flask's response handling.

## Example 1: Database Connection Conflict

**Location:** `importer.py` lines 319-341

**Problem:** The importer creates a new SQLite connection (`sqlite3.connect(db_path, check_same_thread=False)`) while Flask's request context may already have an active connection via `g._db_conn` from `app/models.py`. When both connections attempt to write to the database simultaneously, SQLite can throw "database is locked" errors or cause transaction conflicts, resulting in a 500 error.

**Code:**
```python
# Connect to database and save trips
db_path = get_database_path()
conn = sqlite3.connect(db_path, check_same_thread=False)  # Creates new connection
conn.row_factory = sqlite3.Row
# ... process trips ...
conn.close()
```

**Impact:** This bypasses Flask's connection pooling and can cause database locking issues, especially under concurrent load or when the Flask app context already has an active connection.

## Example 2: Improper Error Response Format

**Location:** `app/routes.py` lines 1611, 1762

**Problem:** The route handler returns `render_template('import_excel.html'), 500` which is not the correct Flask syntax for error responses. Flask expects either a tuple of `(response, status_code)` where response is a string/Response object, or using `make_response()`. When an exception occurs during template rendering or the response format is incorrect, Flask may fail to handle it properly, resulting in an unhandled 500 error.

**Code:**
```python
return render_template('import_excel.html'), 500  # Incorrect format
```

**Impact:** Flask may not properly set the HTTP status code, or the template rendering may fail silently, causing the user to see a generic 500 error page instead of the intended error message.

