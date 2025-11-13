#!/bin/bash
# Build script for ComplyEur assets - bundles and minifies CSS/JS for production
# Part of Lighthouse 5-star optimization initiative
# Compatible with Render.com deployment (handles missing npm tools gracefully)

# Don't exit on error - handle failures gracefully
set +e

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
# Check if all CSS files exist before concatenating
MISSING_CSS=""
for css_file in "$CSS_DIR/global.css" "$CSS_DIR/components.css" "$CSS_DIR/hubspot-style.css" \
                "$CSS_DIR/styles.css" "$CSS_DIR/phase3-enhancements.css" "$CSS_DIR/cookie-footer.css"; do
    if [ ! -f "$css_file" ]; then
        MISSING_CSS="$MISSING_CSS $css_file"
    fi
done

if [ -n "$MISSING_CSS" ]; then
    echo "⚠️  Warning: Some CSS files are missing:$MISSING_CSS"
    echo "   Creating bundle with available files..."
    # Only concatenate files that exist
    > "$BUNDLE_CSS"  # Create empty file
    for css_file in "$CSS_DIR/global.css" "$CSS_DIR/components.css" "$CSS_DIR/hubspot-style.css" \
                    "$CSS_DIR/styles.css" "$CSS_DIR/phase3-enhancements.css" "$CSS_DIR/cookie-footer.css"; do
        if [ -f "$css_file" ]; then
            cat "$css_file" >> "$BUNDLE_CSS"
        fi
    done
else
    cat "$CSS_DIR/global.css" \
        "$CSS_DIR/components.css" \
        "$CSS_DIR/hubspot-style.css" \
        "$CSS_DIR/styles.css" \
        "$CSS_DIR/phase3-enhancements.css" \
        "$CSS_DIR/cookie-footer.css" > "$BUNDLE_CSS"
fi

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
# Check if all JS files exist before concatenating
MISSING_JS=""
for js_file in "$JS_DIR/utils.js" "$JS_DIR/validation.js" "$JS_DIR/notifications.js" \
               "$JS_DIR/keyboard-shortcuts.js" "$JS_DIR/hubspot-style.js" "$JS_DIR/cookie-consent.js"; do
    if [ ! -f "$js_file" ]; then
        MISSING_JS="$MISSING_JS $js_file"
    fi
done

if [ -n "$MISSING_JS" ]; then
    echo "⚠️  Warning: Some JavaScript files are missing:$MISSING_JS"
    echo "   Creating bundle with available files..."
    # Only concatenate files that exist
    > "$BUNDLE_JS"  # Create empty file
    for js_file in "$JS_DIR/utils.js" "$JS_DIR/validation.js" "$JS_DIR/notifications.js" \
                   "$JS_DIR/keyboard-shortcuts.js" "$JS_DIR/hubspot-style.js" "$JS_DIR/cookie-consent.js"; do
        if [ -f "$js_file" ]; then
            cat "$js_file" >> "$BUNDLE_JS"
        fi
    done
else
    cat "$JS_DIR/utils.js" \
        "$JS_DIR/validation.js" \
        "$JS_DIR/notifications.js" \
        "$JS_DIR/keyboard-shortcuts.js" \
        "$JS_DIR/hubspot-style.js" \
        "$JS_DIR/cookie-consent.js" > "$BUNDLE_JS"
fi

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
# Check if bundles were created successfully
if [ -f "$BUNDLE_CSS" ] && [ -f "$BUNDLE_JS" ]; then
    echo "✅ Build complete!"
    echo ""
    echo "📊 Summary:"
    echo "   CSS Bundle: $CSS_SIZE"
    echo "   JS Bundle: $JS_SIZE"
    echo ""
    echo "💡 To use minified versions, update templates to reference:"
    echo "   - css/bundle.min.css"
    echo "   - js/bundle.min.js"
    exit 0
else
    echo "⚠️  Build completed with warnings - some bundles may be missing"
    echo "   Application will continue to work using individual CSS/JS files"
    exit 0  # Don't fail - app works without bundles
fi


