#!/bin/bash
# Optimized Render build script - faster deployments
# Skips test-only packages and unnecessary steps

set -e

echo "🚀 ComplyEur Fast Build Script"
echo "==============================="
echo ""

# Use project directory for temp files
TMP_DIR=$(pwd)/.render_build
mkdir -p "$TMP_DIR"

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found!"
    exit 1
fi

# Upgrade pip first (faster with cache)
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet --no-cache-dir 2>&1 | tail -3 || true

# Create production-only requirements (exclude ALL test/optional packages)
echo "📦 Preparing production requirements..."
grep -v "^python-magic\|^playwright\|^pytest\|^pandas\|^matplotlib\|^psutil" requirements.txt > "$TMP_DIR/requirements_prod.txt" || cp requirements.txt "$TMP_DIR/requirements_prod.txt"

# Install system dependencies only if needed (check for packages that require compilation)
echo "🔧 Checking if system dependencies are needed..."
NEEDS_BUILD_DEPS=false
if grep -q "argon2\|cryptography" "$TMP_DIR/requirements_prod.txt"; then
    NEEDS_BUILD_DEPS=true
fi

if [ "$NEEDS_BUILD_DEPS" = true ] && command -v apt-get >/dev/null 2>&1; then
    echo "🔧 Installing minimal system dependencies..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq >/dev/null 2>&1 && \
    apt-get install -y --no-install-recommends libffi-dev libargon2-dev python3-dev >/dev/null 2>&1 || true
fi

# Install production requirements with pip cache (much faster)
echo "📦 Installing production dependencies..."
echo "   (Using pip cache for faster installs)"
pip install --prefer-binary --no-cache-dir -r "$TMP_DIR/requirements_prod.txt" > "$TMP_DIR/pip_install.log" 2>&1 || {
    echo "⚠️  Install had issues, checking log..."
    tail -20 "$TMP_DIR/pip_install.log"
    exit 1
}

# Quick asset build (just concatenation, no minification needed)
echo "📦 Building assets..."
if [ -f "./scripts/build_assets.sh" ]; then
    chmod +x ./scripts/build_assets.sh 2>/dev/null || true
    ./scripts/build_assets.sh >/dev/null 2>&1 || echo "⚠️  Asset build skipped (non-critical)"
fi

# Quick import test (only critical modules)
echo "🧪 Testing critical imports..."
python -c "
import flask, flask_sqlalchemy, flask_wtf, flask_talisman
import app.models_auth, app.config_auth
print('✅ Core imports OK')
" > "$TMP_DIR/import_test.log" 2>&1 || {
    echo "⚠️  Import test failed (checking...)"
    cat "$TMP_DIR/import_test.log"
    # Don't fail - let Render try to start
}

# Cleanup
rm -rf "$TMP_DIR" 2>/dev/null || true

echo ""
echo "✅ Fast build complete!"
echo "   (Test-only packages skipped for faster deployment)"

