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
if ! pip install --upgrade pip setuptools wheel; then
    echo "⚠️  Warning: Failed to upgrade pip, continuing anyway..."
fi

if ! pip install -r "$TMP_DIR/requirements_core.txt"; then
    echo ""
    echo "❌ ERROR: Core dependencies failed to install"
    echo "   This is a critical failure - the build cannot continue"
    echo "   Check the error messages above for details"
    echo ""
    # Show the core requirements for debugging
    echo "Core requirements that should be installed:"
    cat "$TMP_DIR/requirements_core.txt"
    echo ""
    echo "Python version: $(python --version 2>&1)"
    echo "Pip version: $(pip --version 2>&1)"
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

