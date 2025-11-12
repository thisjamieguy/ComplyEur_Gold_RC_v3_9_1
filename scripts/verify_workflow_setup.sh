#!/bin/bash

# ComplyEur Workflow Setup Verification Script
# Verifies that all workflow components are properly configured

set -e

# Colours
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ComplyEur Workflow Setup Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ERRORS=0
WARNINGS=0

# Check if in Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ Not in a Git repository${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Git repository detected${NC}"
fi

# Check VERSION file
if [ ! -f "VERSION" ]; then
    echo -e "${RED}✗ VERSION file not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    VERSION=$(head -n 1 VERSION | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
    if [ -z "$VERSION" ]; then
        echo -e "${RED}✗ Could not parse version from VERSION file${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ VERSION file found: ${VERSION}${NC}"
    fi
fi

# Check CHANGELOG.md
if [ ! -f "CHANGELOG.md" ]; then
    echo -e "${YELLOW}⚠ CHANGELOG.md not found (will be created on first update)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ CHANGELOG.md found${NC}"
fi

# Check version bump script
if [ ! -f "scripts/bump_version.sh" ]; then
    echo -e "${RED}✗ scripts/bump_version.sh not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    if [ -x "scripts/bump_version.sh" ]; then
        echo -e "${GREEN}✓ scripts/bump_version.sh exists and is executable${NC}"
    else
        echo -e "${YELLOW}⚠ scripts/bump_version.sh exists but is not executable${NC}"
        echo "  Run: chmod +x scripts/bump_version.sh"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check changelog update script
if [ ! -f "scripts/update_changelog.sh" ]; then
    echo -e "${RED}✗ scripts/update_changelog.sh not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    if [ -x "scripts/update_changelog.sh" ]; then
        echo -e "${GREEN}✓ scripts/update_changelog.sh exists and is executable${NC}"
    else
        echo -e "${YELLOW}⚠ scripts/update_changelog.sh exists but is not executable${NC}"
        echo "  Run: chmod +x scripts/update_changelog.sh"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check GitHub Actions workflow
if [ ! -f ".github/workflows/version_release.yml" ]; then
    echo -e "${RED}✗ .github/workflows/version_release.yml not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ GitHub Actions workflow found${NC}"
fi

# Check workflow documentation
if [ ! -f "docs/WORKFLOW.md" ]; then
    echo -e "${YELLOW}⚠ docs/WORKFLOW.md not found${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Workflow documentation found${NC}"
fi

# Check for main branch
if git show-ref --verify --quiet refs/heads/main; then
    echo -e "${GREEN}✓ main branch exists${NC}"
else
    echo -e "${YELLOW}⚠ main branch not found locally${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for develop branch
if git show-ref --verify --quiet refs/heads/develop; then
    echo -e "${GREEN}✓ develop branch exists${NC}"
else
    echo -e "${YELLOW}⚠ develop branch not found locally${NC}"
    echo "  To create: git checkout -b develop"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for origin remote
if git remote | grep -q "^origin$"; then
    echo -e "${GREEN}✓ origin remote configured${NC}"
else
    echo -e "${YELLOW}⚠ origin remote not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Workflow is ready to use.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Setup complete with ${WARNINGS} warning(s)${NC}"
    exit 0
else
    echo -e "${RED}✗ Setup incomplete: ${ERRORS} error(s), ${WARNINGS} warning(s)${NC}"
    exit 1
fi

