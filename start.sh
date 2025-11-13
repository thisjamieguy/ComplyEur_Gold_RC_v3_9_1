#!/bin/bash
# Render startup script - ensures environment is correct before starting gunicorn

set -e

echo "🚀 ComplyEur Startup Script"
echo "================================"
echo ""

# Show environment
echo "📋 Environment Variables:"
echo "  FLASK_ENV: ${FLASK_ENV:-not set}"
echo "  RENDER: ${RENDER:-not set}"
echo "  DATABASE_PATH: ${DATABASE_PATH:-not set}"
echo "  SQLALCHEMY_DATABASE_URI: ${SQLALCHEMY_DATABASE_URI:-not set}"
echo "  PERSISTENT_DIR: ${PERSISTENT_DIR:-not set}"
echo "  SECRET_KEY: ${SECRET_KEY:+[SET]}"
echo ""

# Ensure persistent directory exists and is writable
if [ -n "$PERSISTENT_DIR" ]; then
    echo "📁 Checking persistent directory: $PERSISTENT_DIR"
    if [ ! -d "$PERSISTENT_DIR" ]; then
        echo "❌ ERROR: Persistent directory does not exist: $PERSISTENT_DIR"
        exit 1
    fi
    if [ ! -w "$PERSISTENT_DIR" ]; then
        echo "❌ ERROR: Persistent directory is not writable: $PERSISTENT_DIR"
        exit 1
    fi
    echo "✅ Persistent directory is ready"
else
    echo "⚠️  Warning: PERSISTENT_DIR not set (using local paths)"
fi

# Check if SECRET_KEY is set
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is not set!"
    echo "   Please set SECRET_KEY in Render dashboard > Environment"
    exit 1
fi
echo "✅ SECRET_KEY is configured"

# Test Python environment
echo ""
echo "🐍 Python Environment:"
python --version
echo "  Pip version: $(pip --version)"
echo ""

# Test critical imports
echo "🧪 Testing critical imports..."
python -c "
import sys
try:
    import flask
    import gunicorn
    print('✅ Flask and Gunicorn imported')
    
    # Test app can be imported
    from app.__init__auth__ import create_app
    print('✅ App factory imported')
    
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Import test failed - cannot start application"
    exit 1
fi

echo ""
echo "✅ All startup checks passed!"
echo ""
echo "🚀 Starting Gunicorn..."
echo "================================"
echo ""

# Start gunicorn with proper configuration
exec gunicorn wsgi:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

