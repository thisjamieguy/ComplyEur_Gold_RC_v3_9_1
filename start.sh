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

if [ -z "$PERSISTENT_DIR" ]; then
    echo "❌ ERROR: PERSISTENT_DIR environment variable is required."
    exit 1
fi

if [ -z "$DATABASE_PATH" ]; then
    echo "❌ ERROR: DATABASE_PATH environment variable is required."
    exit 1
fi

resolve_path() {
    local path="$1"
    path="${path#./}"
    if [[ "$path" = /* ]]; then
        printf "%s" "$path"
    elif [ -n "$PERSISTENT_DIR" ]; then
        printf "%s/%s" "$PERSISTENT_DIR" "$path"
    else
        printf "%s/%s" "$(pwd)" "$path"
    fi
}

ensure_dir() {
    local dir="$1"
    if [ -z "$dir" ]; then
        return
    fi
    mkdir -p "$dir" 2>/dev/null || true
    if [ ! -d "$dir" ]; then
        echo "❌ ERROR: Unable to create directory: $dir"
        exit 1
    fi
    if [ ! -w "$dir" ]; then
        echo "❌ ERROR: Directory not writable: $dir"
        exit 1
    fi
}

# Ensure persistent directory exists and is writable
echo "📁 Checking persistent directory: $PERSISTENT_DIR"
ensure_dir "$PERSISTENT_DIR"
echo "✅ Persistent directory is ready"

# Resolve DATABASE_PATH and ensure directory exists
RESOLVED_DB_PATH=$(resolve_path "${DATABASE_PATH:-data/eu_tracker.db}")
export DATABASE_PATH="$RESOLVED_DB_PATH"
DB_DIR=$(dirname "$RESOLVED_DB_PATH")
ensure_dir "$DB_DIR"

# Prepare persistent subdirectories (logs, exports, uploads, backups)
PERSISTENT_BASE="${PERSISTENT_DIR:-$DB_DIR}"
ensure_dir "$PERSISTENT_BASE/logs"
ensure_dir "$PERSISTENT_BASE/exports"
ensure_dir "$PERSISTENT_BASE/uploads"
ensure_dir "$PERSISTENT_BASE/backups"

# Check if SECRET_KEY is set
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is not set!"
    echo "   Please set SECRET_KEY in Render dashboard > Environment"
    exit 1
fi
echo "✅ SECRET_KEY is configured"

# Check if ADMIN_PASSWORD_HASH is set
if [ -z "$ADMIN_PASSWORD_HASH" ]; then
    echo "❌ ERROR: ADMIN_PASSWORD_HASH environment variable is not set!"
    echo "   Provide an Argon2/bcrypt hash via Render dashboard > Environment"
    exit 1
fi
echo "✅ ADMIN_PASSWORD_HASH is configured"

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
    --capture-output \
    --log-level info

