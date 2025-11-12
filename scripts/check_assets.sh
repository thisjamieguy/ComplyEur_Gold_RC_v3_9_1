#!/bin/bash
# Check frontend asset sizes and loading performance
# Part of ComplyEur performance optimization suite

echo "=========================================="
echo "ComplyEur Asset Size Analysis"
echo "=========================================="
echo ""

echo "=== CSS Files ==="
find app/static/css -name "*.css" -type f -exec ls -lh {} \; | awk '{printf "%-50s %10s\n", $9, $5}' | sort
echo ""

echo "=== JavaScript Files ==="
find app/static/js -name "*.js" -type f -exec ls -lh {} \; | awk '{printf "%-50s %10s\n", $9, $5}' | sort
echo ""

echo "=== Image Files (WebP) ==="
find app/static/images -name "*.webp" -type f -exec ls -lh {} \; | awk '{printf "%-50s %10s\n", $9, $5}' | head -20
echo ""

echo "=== Total Static Assets Size ==="
du -sh app/static/ | awk '{print "Total: " $1}'
echo ""

echo "=== CSS Bundle Analysis ==="
CSS_COUNT=$(find app/static/css -name "*.css" -type f | wc -l)
CSS_TOTAL=$(find app/static/css -name "*.css" -type f -exec du -cb {} + 2>/dev/null | tail -1 | awk '{print $1}')
echo "CSS Files: $CSS_COUNT"
echo "Total CSS Size: $(echo "scale=2; $CSS_TOTAL/1024" | bc)KB"
echo ""

if [ "$CSS_COUNT" -gt 3 ]; then
    echo "⚠️  Recommendation: Consider bundling CSS files (currently $CSS_COUNT files)"
fi

if [ "$CSS_TOTAL" -gt 200000 ]; then
    echo "⚠️  Recommendation: CSS size > 200KB - consider minification"
fi

echo "=========================================="

