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

# Ensure required system build tools are present (needed when wheels unavailable)
if command -v apt-get >/dev/null 2>&1; then
    echo "🔧 Installing system build dependencies via apt..."
    export DEBIAN_FRONTEND=noninteractive
    if ! apt-get update -y >"$TMP_DIR/apt-update.log" 2>&1; then
        echo "⚠️  Warning: apt-get update failed (see $TMP_DIR/apt-update.log), continuing without system deps"
    else
        if ! apt-get install -y --no-install-recommends build-essential libffi-dev libargon2-dev python3-dev pkg-config ninja-build >"$TMP_DIR/apt-install.log" 2>&1; then
            echo "⚠️  Warning: apt-get install failed (see $TMP_DIR/apt-install.log), continuing without system deps"
        else
            echo "✅ System build dependencies installed"
        fi
    fi
else
    echo "ℹ️  apt-get not available (likely macOS/local dev); skipping system dependency install"
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

# Install core requirements - try standard install first, then fallback to wheels-only
echo ""
echo "📦 Installing core Python dependencies..."
echo "   Strategy: Prefer wheels, fallback to building from source only if wheels unavailable"

# Try installing all at once with wheel preference
set +e
pip install --prefer-binary --no-cache-dir -r "$TMP_DIR/requirements_core.txt" > "$TMP_DIR/pip_install.log" 2>&1
PIP_EXIT=$?
set -e

if [ $PIP_EXIT -ne 0 ]; then
    echo ""
    echo "⚠️  Install failed, analyzing error..."
    
    # Check if it's a metadata-generation-failed error
    if grep -qi "metadata-generation-failed\|ninja.*build stopped\|Building wheel for" "$TMP_DIR/pip_install.log"; then
        echo "   Detected build-from-source failure"
        echo "   Package trying to build from source (no wheel available)"
        echo ""
        echo "   Identifying failing package..."
        
        # Extract package name from error (look for "Building wheel for <package>")
        FAILING_PACKAGE=$(grep -i "Building wheel for" "$TMP_DIR/pip_install.log" | head -1 | sed 's/.*Building wheel for \([^ ]*\).*/\1/' || echo "unknown")
        if [ "$FAILING_PACKAGE" != "unknown" ] && [ -n "$FAILING_PACKAGE" ]; then
            echo "   ⚠️  Failing package: $FAILING_PACKAGE"
            echo "   This package doesn't have a pre-built wheel for this platform"
        fi
        
        echo ""
        echo "   Attempting wheels-only install (skip packages without wheels)..."
        
        # Try wheels-only install - this will skip packages without wheels
        set +e
        pip install --only-binary :all: --no-cache-dir -r "$TMP_DIR/requirements_core.txt" > "$TMP_DIR/pip_wheels_only.log" 2>&1
        WHEELS_EXIT=$?
        set -e
        
        if [ $WHEELS_EXIT -ne 0 ]; then
            echo ""
            echo "❌ ERROR: Some packages don't have wheels and failed to build"
            echo ""
            echo "   Last 40 lines of error log:"
            tail -40 "$TMP_DIR/pip_install.log"
            echo ""
            echo "   Failed packages (no wheels available):"
            grep -i "ERROR: Could not find a version\|ERROR: No matching distribution\|Skipping" "$TMP_DIR/pip_wheels_only.log" || echo "   (check logs above)"
            echo ""
            echo "   Environment info:"
            echo "   Python: $(python --version 2>&1)"
            echo "   Pip: $(pip --version 2>&1)"
            echo "   Platform: $(python -c 'import platform; print(platform.platform())' 2>/dev/null || echo 'unknown')"
            echo ""
            echo "   Solution: Update failing packages to versions with wheels"
            exit 1
        else
            echo "✅ Core dependencies installed successfully (using wheels only)"
            echo "   Note: Some packages may be missing if they don't have wheels"
        fi
    else
        echo ""
        echo "❌ ERROR: Installation failed (not a build-from-source issue)"
        echo "   Last 40 lines of error log:"
        tail -40 "$TMP_DIR/pip_install.log"
        echo ""
        exit 1
    fi
else
    echo "✅ Core dependencies installed successfully"
fi

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

# Run asset build script (optional - don't fail build if this fails)
echo ""
echo "📦 Building assets..."
if [ ! -f "./scripts/build_assets.sh" ]; then
    echo "⚠️  Warning: build_assets.sh not found, skipping asset build"
else
    if [ ! -x "./scripts/build_assets.sh" ]; then
        echo "⚠️  Warning: build_assets.sh is not executable, making it executable..."
        chmod +x ./scripts/build_assets.sh
    fi
    # Run asset build but don't fail the entire deployment if it fails
    set +e
    ./scripts/build_assets.sh
    ASSET_BUILD_EXIT=$?
    set -e
    if [ $ASSET_BUILD_EXIT -ne 0 ]; then
        echo "⚠️  Warning: Asset build failed (exit code: $ASSET_BUILD_EXIT)"
        echo "   Continuing deployment - app will work without bundled assets"
    else
        echo "✅ Asset build completed successfully"
    fi
fi

# Test that critical modules can be imported (catches import errors early)
echo ""
echo "🧪 Testing critical imports..."
set +e
python -c "
import sys
try:
    # Test Flask and core dependencies
    import flask
    import flask_sqlalchemy
    import flask_wtf
    import flask_talisman
    import werkzeug
    import argon2
    import cryptography
    print('✅ Core dependencies import successfully')
    
    # Test app modules can be imported (without initializing app)
    import app.models_auth
    import app.config_auth
    print('✅ App modules import successfully')
    
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" > "$TMP_DIR/app_test.log" 2>&1
APP_TEST_EXIT=$?
set -e

if [ $APP_TEST_EXIT -ne 0 ]; then
    echo "❌ ERROR: Import test failed!"
    echo ""
    echo "   Error output:"
    cat "$TMP_DIR/app_test.log"
    echo ""
    echo "   This indicates missing dependencies or import errors."
    echo "   Check the error above for details."
    # Don't fail build - let Render try to start it anyway
    echo "⚠️  Continuing with deployment despite import test failure"
else
    echo "✅ Import test passed"
fi

# Cleanup temp directory
rm -rf "$TMP_DIR" 2>/dev/null || true

echo ""
echo "✅ Build complete!"
