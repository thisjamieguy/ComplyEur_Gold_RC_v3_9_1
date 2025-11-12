#!/bin/bash
# Render build script - handles optional dependencies gracefully
# This script installs requirements, allowing python-magic to fail if system libs are missing

set -e

echo "🔨 ComplyEur Render Build Script"
echo "================================="
echo ""

# Install all requirements (python-magic may fail, but that's OK)
echo "📦 Installing Python dependencies..."
set +e  # Temporarily disable exit on error for pip install
pip install -r requirements.txt
PIP_EXIT=$?
set -e  # Re-enable exit on error

if [ $PIP_EXIT -ne 0 ]; then
    echo "⚠️  Some dependencies failed to install, trying without python-magic..."
    # Create temp requirements without python-magic
    grep -v "^python-magic" requirements.txt > /tmp/requirements_no_magic.txt || true
    set +e
    pip install -r /tmp/requirements_no_magic.txt || pip install -r requirements.txt --ignore-installed python-magic || true
    set -e
    echo "⚠️  Continuing with available packages (python-magic is optional)"
fi

# Try to install python-magic separately (optional - may fail on Render)
echo ""
echo "📦 Attempting to install python-magic (optional)..."
set +e
pip install python-magic==0.4.27 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  python-magic installation skipped (requires system libmagic)"
    echo "   Application will use fallback MIME type detection"
fi
set -e

# Run asset build script
echo ""
echo "📦 Building assets..."
./scripts/build_assets.sh

echo ""
echo "✅ Build complete!"

