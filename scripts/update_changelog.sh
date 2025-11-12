#!/bin/bash

# ComplyEur Changelog Update Script
# Automatically generates changelog entries from Git commits since last tag
#
# Usage: ./scripts/update_changelog.sh
#
# This script:
#   1. Finds the latest Git tag
#   2. Extracts commits since that tag
#   3. Formats them according to Keep a Changelog standards
#   4. Prepends to CHANGELOG.md
#   5. Commits the changelog update

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a Git repository${NC}"
    exit 1
fi

# Check if CHANGELOG.md exists
if [ ! -f "CHANGELOG.md" ]; then
    echo -e "${RED}Error: CHANGELOG.md not found${NC}"
    exit 1
fi

# Get current version from VERSION file
if [ ! -f "VERSION" ]; then
    echo -e "${RED}Error: VERSION file not found${NC}"
    exit 1
fi

CURRENT_VERSION=$(head -n 1 VERSION | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}Error: Could not parse version from VERSION file${NC}"
    exit 1
fi

# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
    echo -e "${YELLOW}No tags found. Using all commits.${NC}"
    COMMIT_RANGE="HEAD"
else
    echo -e "${YELLOW}Latest tag: ${LATEST_TAG}${NC}"
    COMMIT_RANGE="${LATEST_TAG}..HEAD"
fi

# Get current date
RELEASE_DATE=$(date +%Y-%m-%d)

# Get commits since last tag (or all commits if no tag)
COMMITS=$(git log ${COMMIT_RANGE} --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}No new commits since last tag${NC}"
    exit 0
fi

# Categorise commits
ADDED=()
FIXED=()
CHANGED=()
SECURITY=()
REMOVED=()
OTHER=()

while IFS= read -r commit; do
    # Skip empty lines
    [ -z "$commit" ] && continue
    
    # Categorise by conventional commit prefix
    if [[ "$commit" =~ ^(feat|add|added|new): ]]; then
        ADDED+=("$commit")
    elif [[ "$commit" =~ ^(fix|fixed|bugfix): ]]; then
        FIXED+=("$commit")
    elif [[ "$commit" =~ ^(change|changed|update|refactor): ]]; then
        CHANGED+=("$commit")
    elif [[ "$commit" =~ ^(security|sec): ]]; then
        SECURITY+=("$commit")
    elif [[ "$commit" =~ ^(remove|removed|delete): ]]; then
        REMOVED+=("$commit")
    else
        OTHER+=("$commit")
    fi
done <<< "$COMMITS"

# Build changelog entry
CHANGELOG_ENTRY="## [${CURRENT_VERSION}] - ${RELEASE_DATE}\n\n"

# Add sections only if they have content
if [ ${#ADDED[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Added\n"
    for item in "${ADDED[@]}"; do
        # Remove conventional commit prefix for display
        CLEANED=$(echo "$item" | sed -E 's/^(feat|add|added|new):\s*//i')
        CHANGELOG_ENTRY+="- ${CLEANED}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Fixed\n"
    for item in "${FIXED[@]}"; do
        CLEANED=$(echo "$item" | sed -E 's/^(fix|fixed|bugfix):\s*//i')
        CHANGELOG_ENTRY+="- ${CLEANED}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Changed\n"
    for item in "${CHANGED[@]}"; do
        CLEANED=$(echo "$item" | sed -E 's/^(change|changed|update|refactor):\s*//i')
        CHANGELOG_ENTRY+="- ${CLEANED}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

if [ ${#SECURITY[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Security\n"
    for item in "${SECURITY[@]}"; do
        CLEANED=$(echo "$item" | sed -E 's/^(security|sec):\s*//i')
        CHANGELOG_ENTRY+="- ${CLEANED}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Removed\n"
    for item in "${REMOVED[@]}"; do
        CLEANED=$(echo "$item" | sed -E 's/^(remove|removed|delete):\s*//i')
        CHANGELOG_ENTRY+="- ${CLEANED}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

if [ ${#OTHER[@]} -gt 0 ]; then
    CHANGELOG_ENTRY+="### Other\n"
    for item in "${OTHER[@]}"; do
        CHANGELOG_ENTRY+="- ${item}\n"
    done
    CHANGELOG_ENTRY+="\n"
fi

CHANGELOG_ENTRY+="---\n\n"

# Read existing changelog
CHANGELOG_CONTENT=$(cat CHANGELOG.md)

# Find where to insert (after the header section, before first existing version)
# Look for the first "## [" entry
if [[ "$CHANGELOG_CONTENT" =~ ^(.*)(## \[) ]]; then
    HEADER="${BASH_REMATCH[1]}"
    REMAINING="${CHANGELOG_CONTENT#*## \[}"
    REMAINING="## [${REMAINING}"
    
    # Insert new entry
    NEW_CHANGELOG="${HEADER}${CHANGELOG_ENTRY}${REMAINING}"
else
    # No existing version entries, append to end
    NEW_CHANGELOG="${CHANGELOG_CONTENT}\n\n${CHANGELOG_ENTRY}"
fi

# Write updated changelog
echo -e "$NEW_CHANGELOG" > CHANGELOG.md

echo -e "${GREEN}✓ Updated CHANGELOG.md${NC}"

# Stage changelog
git add CHANGELOG.md

# Commit with conventional commit message
COMMIT_MSG="docs: update CHANGELOG for v${CURRENT_VERSION}"
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}✓ Committed changelog update${NC}"

# Check if remote exists
if git remote | grep -q "^origin$"; then
    echo -e "${YELLOW}Pushing to origin...${NC}"
    git push origin HEAD
    echo -e "${GREEN}✓ Pushed changelog update to origin${NC}"
else
    echo -e "${YELLOW}No 'origin' remote found. Skipping push.${NC}"
    echo "To push manually: git push origin HEAD"
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Changelog updated for version ${CURRENT_VERSION}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

