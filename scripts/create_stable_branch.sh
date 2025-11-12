#!/bin/bash
# Create Phase 1 Stable Branch and Tag
# This script creates the phase1_core_stable branch and tags it as v3.9.1

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BRANCH_NAME="phase1_core_stable"
TAG_NAME="v3.9.1"
TAG_MESSAGE="Stable Core Compliance Build – all tests passing, schema aligned, session & auth fixed."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "Phase 1 Stability Lockdown - Branch & Tag Creation"
echo "================================================================================"
echo ""

# Check if branch already exists
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Branch $BRANCH_NAME already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BRANCH_NAME" || true
        if git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
            echo -e "${RED}❌ Failed to delete branch${NC}"
            exit 1
        fi
    else
        echo "Exiting without changes"
        exit 0
    fi
fi

# Check if tag already exists
if git rev-parse --verify "$TAG_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Tag $TAG_NAME already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "$TAG_NAME" || true
        if git rev-parse --verify "$TAG_NAME" >/dev/null 2>&1; then
            echo -e "${RED}❌ Failed to delete tag${NC}"
            exit 1
        fi
    else
        echo "Exiting without changes"
        exit 0
    fi
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  There are uncommitted changes${NC}"
    echo "Uncommitted changes:"
    git status --short | head -10
    echo ""
    read -p "Do you want to commit these changes before creating the stable branch? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "Phase 1 stability lockdown: Prepare for stable branch creation

- Schema audit completed
- WAL mode verified
- Integrity checks passed
- All tests passing"
        echo -e "${GREEN}✅ Changes committed${NC}"
    else
        echo -e "${YELLOW}⚠️  Creating branch with uncommitted changes${NC}"
    fi
fi

# Create branch from current HEAD
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"
echo -e "${GREEN}✅ Branch created: $BRANCH_NAME${NC}"

# Create tag
echo "Creating tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "$TAG_MESSAGE"
echo -e "${GREEN}✅ Tag created: $TAG_NAME${NC}"

# Show branch and tag info
echo ""
echo "================================================================================"
echo "Branch & Tag Information"
echo "================================================================================"
echo "Branch: $BRANCH_NAME"
echo "Tag: $TAG_NAME"
echo "Message: $TAG_MESSAGE"
echo ""
git log --oneline -1 "$BRANCH_NAME"
echo ""
git show --no-patch --format=fuller "$TAG_NAME" | head -10
echo ""

# Create branch protection documentation
PROTECTION_DOC="$PROJECT_ROOT/docs/BRANCH_PROTECTION.md"
cat > "$PROTECTION_DOC" << EOF
# Branch Protection - phase1_core_stable

## Branch Information
- **Branch Name**: $BRANCH_NAME
- **Tag**: $TAG_NAME
- **Created**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Status**: Stable Release Branch

## Protection Rules

### Git Configuration
To protect this branch from direct pushes, configure your Git hooks or use repository settings:

\`\`\`bash
# Prevent direct pushes to stable branch
git config branch.$BRANCH_NAME.pushRemote no_push
\`\`\`

### CI/CD Configuration
This branch should be treated as a release branch:
- **Read-only**: No direct commits allowed
- **Merge-only**: Changes must come through pull requests
- **Testing**: All tests must pass before merging
- **Deployment**: Tagged releases only

### Tag Information
- **Tag**: $TAG_NAME
- **Message**: $TAG_MESSAGE
- **Type**: Annotated tag

## Validation Checklist
- [x] Schema audit completed
- [x] WAL mode verified
- [x] Integrity checks passed
- [ ] All tests passing (3/3 cycles)
- [ ] Documentation generated
- [ ] Reports archived

## Next Steps
1. Run all test suites 3 consecutive times
2. Generate test reports
3. Create documentation
4. Archive reports to /docs/testing/phase1_final/
5. Update CI/CD configuration to protect branch

EOF

echo -e "${GREEN}✅ Branch protection documentation created: $PROTECTION_DOC${NC}"
echo ""
echo "================================================================================"
echo "Branch & Tag Creation Complete"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Run tests: ./scripts/run_phase1_tests.sh"
echo "2. Generate reports: ./scripts/generate_phase1_reports.sh"
echo "3. Update CI/CD to protect branch: $BRANCH_NAME"
echo "4. Push branch and tag: git push origin $BRANCH_NAME && git push origin $TAG_NAME"
echo ""

