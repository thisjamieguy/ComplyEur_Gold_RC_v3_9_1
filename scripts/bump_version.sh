#!/bin/bash

# ComplyEur Version Bump Script
# Automates semantic versioning increments and Git tagging
#
# Usage: ./scripts/bump_version.sh [major|minor|patch]
#
# This script:
#   1. Reads current version from VERSION file
#   2. Increments based on argument (major/minor/patch)
#   3. Updates VERSION file
#   4. Commits with conventional commit message
#   5. Creates Git tag
#   6. Pushes commit and tag to remote

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

# Check if version type argument is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version type required${NC}"
    echo "Usage: ./scripts/bump_version.sh [major|minor|patch]"
    exit 1
fi

VERSION_TYPE=$1

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED}Error: Invalid version type '${VERSION_TYPE}'${NC}"
    echo "Must be one of: major, minor, patch"
    exit 1
fi

# Check if VERSION file exists
if [ ! -f "VERSION" ]; then
    echo -e "${RED}Error: VERSION file not found${NC}"
    exit 1
fi

# Read current version from VERSION file
# Handle format: "3.9.1 – Gold Release Candidate" or "3.9.1"
CURRENT_VERSION=$(head -n 1 VERSION | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}Error: Could not parse version from VERSION file${NC}"
    exit 1
fi

echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Parse version components
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# Increment version based on type
case $VERSION_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a Git repository${NC}"
    exit 1
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    echo "Consider committing or stashing them before bumping version"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update VERSION file
# Preserve any additional lines after the version
VERSION_CONTENT=$(cat VERSION)
VERSION_LINE=$(echo "$VERSION_CONTENT" | head -n 1)
REMAINING_LINES=$(echo "$VERSION_CONTENT" | tail -n +2)

# Update first line with new version, preserve rest
{
    echo "${NEW_VERSION}"
    if [ -n "$REMAINING_LINES" ]; then
        echo "$REMAINING_LINES"
    fi
} > VERSION

# Stage VERSION file
git add VERSION

# Commit with conventional commit message
COMMIT_MSG="chore: bump version to ${NEW_VERSION}"
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}✓ Committed version bump${NC}"

# Create tag
TAG_NAME="v${NEW_VERSION}"
git tag -a "$TAG_NAME" -m "Release ${NEW_VERSION}"

echo -e "${GREEN}✓ Created tag: ${TAG_NAME}${NC}"

# Check if remote exists
if git remote | grep -q "^origin$"; then
    echo -e "${YELLOW}Pushing to origin...${NC}"
    git push origin HEAD
    git push origin "$TAG_NAME"
    echo -e "${GREEN}✓ Pushed commit and tag to origin${NC}"
else
    echo -e "${YELLOW}No 'origin' remote found. Skipping push.${NC}"
    echo "To push manually:"
    echo "  git push origin HEAD"
    echo "  git push origin ${TAG_NAME}"
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Version bump complete: ${CURRENT_VERSION} → ${NEW_VERSION}${NC}"
echo -e "${GREEN}Tag created: ${TAG_NAME}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

