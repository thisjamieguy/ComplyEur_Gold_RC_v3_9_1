#!/usr/bin/env python3

import os
from app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', '5001'))
    host = os.getenv('HOST', '0.0.0.0')
    app.run(debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true', host=host, port=port, use_reloader=False)
