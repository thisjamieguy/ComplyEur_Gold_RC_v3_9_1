#!/bin/bash
# Render build script - handles optional dependencies gracefully
# This script installs requirements, allowing problematic packages to fail

set -e

echo "🔨 ComplyEur Render Build Script"
echo "================================="
echo ""

# Create requirements file without problematic packages
echo "📦 Preparing requirements (excluding optional/problematic packages)..."
grep -v "^python-magic\|^playwright" requirements.txt > /tmp/requirements_core.txt

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

# Try playwright separately (optional - very large, may fail)
echo ""
echo "📦 Attempting to install playwright (optional)..."
set +e
pip install playwright==1.55.0 2>&1 | grep -E "(error|failed|ninja|metadata-generation)" > /tmp/playwright_error.log 2>&1 || true
PLAYWRIGHT_EXIT=$?
set -e
if [ $PLAYWRIGHT_EXIT -ne 0 ]; then
    echo "⚠️  playwright installation skipped (large dependency, not required for production)"
fi

# Run asset build script
echo ""
echo "📦 Building assets..."
./scripts/build_assets.sh

echo ""
echo "✅ Build complete!"

