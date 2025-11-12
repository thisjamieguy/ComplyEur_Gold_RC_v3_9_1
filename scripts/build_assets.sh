#!/bin/bash
# Build script for ComplyEur assets - bundles and minifies CSS/JS for production
# Part of Lighthouse 5-star optimization initiative
# Compatible with Render.com deployment (handles missing npm tools gracefully)

set -e

echo "🚀 ComplyEur Asset Build Script"
echo "================================"
echo ""

CSS_DIR="app/static/css"
JS_DIR="app/static/js"
BUNDLE_CSS="$CSS_DIR/bundle.css"
MINIFIED_CSS="$CSS_DIR/bundle.min.css"
BUNDLE_JS="$JS_DIR/bundle.js"
MINIFIED_JS="$JS_DIR/bundle.min.js"

# Ensure directories exist
mkdir -p "$CSS_DIR" "$JS_DIR"

# Build CSS Bundle
echo "📦 Bundling CSS files..."
cat "$CSS_DIR/global.css" \
    "$CSS_DIR/components.css" \
    "$CSS_DIR/hubspot-style.css" \
    "$CSS_DIR/styles.css" \
    "$CSS_DIR/phase3-enhancements.css" \
    "$CSS_DIR/cookie-footer.css" > "$BUNDLE_CSS"

CSS_SIZE=$(du -h "$BUNDLE_CSS" | cut -f1)
echo "✅ CSS bundled: $CSS_SIZE"

# Minify CSS (simple minification if csso not available)
if command -v csso &> /dev/null; then
    echo "🔨 Minifying CSS with csso..."
    csso "$BUNDLE_CSS" -o "$MINIFIED_CSS" --comments none
    MIN_SIZE=$(du -h "$MINIFIED_CSS" | cut -f1)
    echo "✅ CSS minified: $MIN_SIZE"
else
    echo "⚠️  csso-cli not found. Using bundled CSS (not minified)"
    echo "   Install with: npm install -g csso-cli"
    cp "$BUNDLE_CSS" "$MINIFIED_CSS"
fi

# Build JavaScript Bundle (core files only - keep help-system, customization, interactive-tutorials separate for async loading)
echo ""
echo "📦 Bundling JavaScript files..."
cat "$JS_DIR/utils.js" \
    "$JS_DIR/validation.js" \
    "$JS_DIR/notifications.js" \
    "$JS_DIR/keyboard-shortcuts.js" \
    "$JS_DIR/hubspot-style.js" \
    "$JS_DIR/cookie-consent.js" > "$BUNDLE_JS"

JS_SIZE=$(du -h "$BUNDLE_JS" | cut -f1)
echo "✅ JavaScript bundled: $JS_SIZE"

# Minify JavaScript (simple minification if terser not available)
if command -v terser &> /dev/null; then
    echo "🔨 Minifying JavaScript with terser..."
    terser "$BUNDLE_JS" -o "$MINIFIED_JS" --compress --mangle --comments false
    MIN_JS_SIZE=$(du -h "$MINIFIED_JS" | cut -f1)
    echo "✅ JavaScript minified: $MIN_JS_SIZE"
else
    echo "⚠️  terser not found. Using bundled JS (not minified)"
    echo "   Install with: npm install -g terser"
    cp "$BUNDLE_JS" "$MINIFIED_JS"
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "📊 Summary:"
echo "   CSS Bundle: $CSS_SIZE"
echo "   JS Bundle: $JS_SIZE"
echo ""
echo "💡 To use minified versions, update templates to reference:"
echo "   - css/bundle.min.css"
echo "   - js/bundle.min.js"


