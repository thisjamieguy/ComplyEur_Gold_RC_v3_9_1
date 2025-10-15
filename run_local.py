#!/usr/bin/env python3

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("Starting Flask development server...")
    print("Visit: http://localhost:5004")
    app.run(debug=True, host='127.0.0.1', port=5004, use_reloader=False)
