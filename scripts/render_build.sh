#!/bin/bash
# Render build script - handles optional dependencies gracefully
# This script installs requirements, allowing problematic packages to fail

set -e

echo "🔨 ComplyEur Render Build Script"
echo "================================="
echo ""

# Create requirements file without problematic/test-only packages
echo "📦 Preparing requirements (excluding optional/test-only packages)..."
# Exclude: python-magic (optional, has fallback), playwright (test-only), 
#          pytest packages (test-only), pandas/matplotlib/psutil (test-only, large)
grep -v "^python-magic\|^playwright\|^pytest\|^pandas\|^matplotlib\|^psutil" requirements.txt > /tmp/requirements_core.txt

# Install core requirements (these must succeed)
echo "📦 Installing core Python dependencies..."
pip install -r /tmp/requirements_core.txt

# Try python-magic separately (optional - requires system libmagic, may fail compilation)
echo ""
echo "📦 Attempting to install python-magic (optional)..."
set +e
pip install python-magic==0.4.27 2>&1 | grep -E "(error|failed|ninja|metadata-generation)" > /tmp/magic_error.log 2>&1 || true
MAGIC_EXIT=$?
set -e
if [ $MAGIC_EXIT -ne 0 ]; then
    echo "⚠️  python-magic installation skipped (requires system libmagic)"
    echo "   Application will use fallback MIME type detection"
fi

# Try test-only packages separately (optional - not needed for production)
echo ""
echo "📦 Attempting to install test-only packages (optional)..."
set +e
# These are only used in tests, not in production
pip install pytest==8.3.3 pytest-flask==1.3.0 2>&1 | grep -E "(error|failed|ninja|metadata-generation)" > /tmp/pytest_error.log 2>&1 || true
pip install pandas==2.2.0 matplotlib==3.8.4 psutil==5.9.8 2>&1 | grep -E "(error|failed|ninja|metadata-generation)" > /tmp/data_error.log 2>&1 || true
pip install playwright==1.55.0 2>&1 | grep -E "(error|failed|ninja|metadata-generation)" > /tmp/playwright_error.log 2>&1 || true
set -e
echo "⚠️  Test packages installation attempted (failures are OK - not required for production)"

# Run asset build script
echo ""
echo "📦 Building assets..."
./scripts/build_assets.sh

echo ""
echo "✅ Build complete!"

