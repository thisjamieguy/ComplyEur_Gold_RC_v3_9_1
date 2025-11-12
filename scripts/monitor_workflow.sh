#!/bin/bash

# Monitor GitHub Actions Workflow Run
# This script monitors a specific workflow run and reports its status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO="thisjamieguy/ComplyEur_Gold_RC_v3_9_1"
WORKFLOW_RUN_ID="${1:-19303346969}"

echo -e "${BLUE}=== ComplyEur Gold RC v3.9.1 - Workflow Monitor ===${NC}"
echo -e "Repository: ${GREEN}$REPO${NC}"
echo -e "Workflow Run ID: ${GREEN}$WORKFLOW_RUN_ID${NC}"
echo ""

# Check if workflow run exists
if ! gh run view "$WORKFLOW_RUN_ID" --repo "$REPO" &>/dev/null; then
    echo -e "${RED}Error: Workflow run $WORKFLOW_RUN_ID not found${NC}"
    exit 1
fi

# Get workflow run status
STATUS=$(gh run view "$WORKFLOW_RUN_ID" --repo "$REPO" --json status --jq .status)
CONCLUSION=$(gh run view "$WORKFLOW_RUN_ID" --repo "$REPO" --json conclusion --jq .conclusion)

echo -e "${BLUE}Workflow Status:${NC}"
echo -e "  Status: ${YELLOW}$STATUS${NC}"
echo -e "  Conclusion: ${YELLOW}${CONCLUSION:-N/A}${NC}"
echo ""

# Get job statuses
echo -e "${BLUE}Job Statuses:${NC}"
gh run view "$WORKFLOW_RUN_ID" --repo "$REPO" --json jobs --jq '.jobs[] | "  \(.name): \(.status) - \(.conclusion // "N/A")"' || true
echo ""

# If workflow is still running, show live status
if [ "$STATUS" = "in_progress" ] || [ "$STATUS" = "queued" ]; then
    echo -e "${YELLOW}Workflow is still running. Monitoring...${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop monitoring${NC}"
    echo ""
    
    # Watch workflow run
    gh run watch "$WORKFLOW_RUN_ID" --repo "$REPO" --exit-status || {
        echo ""
        echo -e "${RED}Workflow failed!${NC}"
        echo -e "${YELLOW}View logs: gh run view $WORKFLOW_RUN_ID --repo $REPO --log-failed${NC}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}Workflow completed successfully!${NC}"
else
    # Show final status
    if [ "$CONCLUSION" = "success" ]; then
        echo -e "${GREEN}✅ Workflow completed successfully!${NC}"
    elif [ "$CONCLUSION" = "failure" ]; then
        echo -e "${RED}❌ Workflow failed!${NC}"
        echo -e "${YELLOW}View failed logs: gh run view $WORKFLOW_RUN_ID --repo $REPO --log-failed${NC}"
        exit 1
    elif [ "$CONCLUSION" = "cancelled" ]; then
        echo -e "${YELLOW}⚠️  Workflow was cancelled${NC}"
    else
        echo -e "${YELLOW}⚠️  Workflow status: $CONCLUSION${NC}"
    fi
fi

echo ""
echo -e "${BLUE}View workflow run:${NC}"
echo -e "  ${GREEN}https://github.com/$REPO/actions/runs/$WORKFLOW_RUN_ID${NC}"
echo ""

