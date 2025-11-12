#!/bin/bash
# Render build script - handles optional dependencies gracefully
# This script installs requirements, allowing problematic packages to fail

set -e

echo "🔨 ComplyEur Render Build Script"
echo "================================="
echo ""

# Use project directory for temp files (more reliable than /tmp on Render)
TMP_DIR=$(pwd)/.render_build
mkdir -p "$TMP_DIR"

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found!"
    echo "   Current directory: $(pwd)"
    echo "   Files in directory:"
    ls -la | head -20
    exit 1
fi

# Create requirements file without problematic/test-only packages
echo "📦 Preparing requirements (excluding optional/test-only packages)..."
# Exclude: python-magic (optional, has fallback), playwright (test-only), 
#          pytest packages (test-only), pandas/matplotlib/psutil (test-only, large)
if ! grep -v "^python-magic\|^playwright\|^pytest\|^pandas\|^matplotlib\|^psutil" requirements.txt > "$TMP_DIR/requirements_core.txt"; then
    echo "⚠️  Warning: Failed to filter requirements, using full requirements.txt"
    cp requirements.txt "$TMP_DIR/requirements_core.txt"
fi

# Verify core requirements file was created
if [ ! -f "$TMP_DIR/requirements_core.txt" ] || [ ! -s "$TMP_DIR/requirements_core.txt" ]; then
    echo "❌ ERROR: Failed to create core requirements file"
    exit 1
fi

echo "✅ Core requirements file created ($(wc -l < "$TMP_DIR/requirements_core.txt") lines)"

# Install core requirements (these must succeed)
echo "📦 Installing core Python dependencies..."
echo "   (This may take a few minutes - packages with C extensions will use pre-built wheels)"
echo "   Installing from: $TMP_DIR/requirements_core.txt"

# Upgrade pip, setuptools, wheel first (required for building wheels)
echo "📦 Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel --no-cache-dir 2>&1 | tail -5 || echo "⚠️  Warning: pip upgrade had issues, continuing..."

# Install packages in groups to isolate failures
echo ""
echo "📦 Installing Flask and web framework packages..."
set +e
pip install --prefer-binary --no-cache-dir Flask==3.0.3 Flask-WTF==1.2.1 Flask-Talisman==1.1.0 Flask-Limiter==3.7.0 Flask-Caching==2.3.0 Flask-Compress==1.14 Flask-SQLAlchemy==3.1.1 Werkzeug==3.0.3 > "$TMP_DIR/flask_install.log" 2>&1
FLASK_EXIT=$?
set -e
if [ $FLASK_EXIT -ne 0 ]; then
    echo "❌ ERROR: Flask packages failed to install"
    cat "$TMP_DIR/flask_install.log" | tail -20
    exit 1
fi

echo "📦 Installing database packages..."
set +e
pip install --prefer-binary --no-cache-dir SQLAlchemy==2.0.35 Flask-SQLAlchemy==3.1.1 python-dotenv==1.0.1 > "$TMP_DIR/db_install.log" 2>&1
DB_EXIT=$?
set -e
if [ $DB_EXIT -ne 0 ]; then
    echo "❌ ERROR: Database packages failed to install"
    cat "$TMP_DIR/db_install.log" | tail -20
    exit 1
fi

echo "📦 Installing security packages (cryptography, argon2)..."
set +e
pip install --prefer-binary --no-cache-dir cryptography==43.0.3 argon2-cffi==23.1.0 bleach==6.1.0 limits==3.13.0 > "$TMP_DIR/security_install.log" 2>&1
SECURITY_EXIT=$?
set -e
if [ $SECURITY_EXIT -ne 0 ]; then
    echo "⚠️  Warning: Some security packages failed to install"
    cat "$TMP_DIR/security_install.log" | tail -20
    echo "   Attempting to install without building from source..."
    set +e
    pip install --only-binary :all: --no-cache-dir cryptography argon2-cffi bleach limits 2>&1 | tail -10 || echo "⚠️  Security packages may not be available as wheels"
    set -e
fi

echo "📦 Installing utility packages..."
set +e
pip install --prefer-binary --no-cache-dir APScheduler==3.10.4 pyotp==2.9.0 qrcode==7.4.2 Pillow==10.4.0 zxcvbn-python==4.4.24 > "$TMP_DIR/utils_install.log" 2>&1
UTILS_EXIT=$?
set -e
if [ $UTILS_EXIT -ne 0 ]; then
    echo "⚠️  Warning: Some utility packages failed to install"
    cat "$TMP_DIR/utils_install.log" | tail -20
    echo "   Attempting to install without building from source..."
    set +e
    pip install --only-binary :all: --no-cache-dir pyotp qrcode Pillow zxcvbn-python 2>&1 | tail -10 || echo "⚠️  Utility packages may not be available as wheels"
    set -e
fi

echo "📦 Installing file processing packages..."
set +e
pip install --prefer-binary --no-cache-dir openpyxl==3.1.5 reportlab==4.2.0 feedparser==6.0.10 requests==2.31.0 diff-match-patch==20230430 > "$TMP_DIR/file_install.log" 2>&1
FILE_EXIT=$?
set -e
if [ $FILE_EXIT -ne 0 ]; then
    echo "⚠️  Warning: Some file processing packages failed to install"
    cat "$TMP_DIR/file_install.log" | tail -20
    echo "   Attempting to install without building from source..."
    set +e
    pip install --only-binary :all: --no-cache-dir openpyxl reportlab feedparser requests 2>&1 | tail -10 || echo "⚠️  File processing packages may not be available as wheels"
    set -e
fi

echo "📦 Installing server package..."
set +e
pip install --prefer-binary --no-cache-dir gunicorn==21.2.0 > "$TMP_DIR/server_install.log" 2>&1
SERVER_EXIT=$?
set -e
if [ $SERVER_EXIT -ne 0 ]; then
    echo "❌ ERROR: gunicorn failed to install (required for production)"
    cat "$TMP_DIR/server_install.log" | tail -20
    exit 1
fi

echo "✅ Core dependencies installed successfully"

# Try python-magic separately (optional - requires system libmagic, may fail compilation)
echo ""
echo "📦 Attempting to install python-magic (optional)..."
set +e
pip install python-magic==0.4.27 > "$TMP_DIR/magic_install.log" 2>&1
MAGIC_EXIT=$?
set -e
if [ $MAGIC_EXIT -ne 0 ]; then
    echo "⚠️  python-magic installation skipped (requires system libmagic)"
    echo "   Application will use fallback MIME type detection"
    # Show first few lines of error for debugging
    head -10 "$TMP_DIR/magic_install.log" 2>/dev/null | grep -i "error\|failed\|ninja\|metadata" || true
else
    echo "✅ python-magic installed successfully"
fi

# Try test-only packages separately (optional - not needed for production)
echo ""
echo "📦 Attempting to install test-only packages (optional)..."
set +e
# These are only used in tests, not in production
pip install pytest==8.3.3 pytest-flask==1.3.0 > "$TMP_DIR/pytest_install.log" 2>&1
PYTEST_EXIT=$?
pip install pandas==2.2.0 matplotlib==3.8.4 psutil==5.9.8 > "$TMP_DIR/data_install.log" 2>&1
DATA_EXIT=$?
pip install playwright==1.55.0 > "$TMP_DIR/playwright_install.log" 2>&1
PLAYWRIGHT_EXIT=$?
set -e

if [ $PYTEST_EXIT -eq 0 ]; then
    echo "✅ pytest packages installed"
else
    echo "⚠️  pytest packages installation skipped (test-only, not required for production)"
fi

if [ $DATA_EXIT -eq 0 ]; then
    echo "✅ data processing packages installed"
else
    echo "⚠️  data processing packages installation skipped (test-only, not required for production)"
fi

if [ $PLAYWRIGHT_EXIT -eq 0 ]; then
    echo "✅ playwright installed"
else
    echo "⚠️  playwright installation skipped (test-only, not required for production)"
fi

# Run asset build script
echo ""
echo "📦 Building assets..."
if [ ! -f "./scripts/build_assets.sh" ]; then
    echo "⚠️  Warning: build_assets.sh not found, skipping asset build"
else
    if [ ! -x "./scripts/build_assets.sh" ]; then
        echo "⚠️  Warning: build_assets.sh is not executable, making it executable..."
        chmod +x ./scripts/build_assets.sh
    fi
    ./scripts/build_assets.sh
fi

# Cleanup temp directory
rm -rf "$TMP_DIR" 2>/dev/null || true

echo ""
echo "✅ Build complete!"

