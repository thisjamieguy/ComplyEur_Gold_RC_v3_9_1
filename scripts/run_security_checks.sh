#!/bin/bash
# Run All Security Checks
# Phase 3: Application Security & Input Validation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔒 Running Security Checks...${NC}"
echo ""

# Install dependencies if needed
if ! command -v bandit &> /dev/null; then
    echo "Installing Bandit..."
    pip install bandit
fi

if ! command -v safety &> /dev/null; then
    echo "Installing Safety..."
    pip install safety
fi

# Run Bandit (SAST)
echo -e "${YELLOW}1. Running Bandit (SAST)...${NC}"
bandit -r app/ -f txt -c .bandit || {
    echo -e "${RED}✗ Bandit found security issues${NC}"
    exit 1
}
echo -e "${GREEN}✓ Bandit scan passed${NC}"
echo ""

# Run Safety (dependency vulnerabilities)
echo -e "${YELLOW}2. Checking dependencies (Safety)...${NC}"
safety check || {
    echo -e "${RED}✗ Safety found vulnerable dependencies${NC}"
    exit 1
}
echo -e "${GREEN}✓ Dependency check passed${NC}"
echo ""

# Run security tests
echo -e "${YELLOW}3. Running security tests...${NC}"
pytest tests/test_auth_security.py tests/test_encryption_security.py tests/test_input_validation.py -v || {
    echo -e "${RED}✗ Security tests failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Security tests passed${NC}"
echo ""

# ESLint (if package.json exists)
if [ -f "package.json" ]; then
    echo -e "${YELLOW}4. Running ESLint...${NC}"
    if command -v eslint &> /dev/null; then
        eslint app/static/js/*.js || {
            echo -e "${YELLOW}⚠ ESLint found issues (non-blocking)${NC}"
        }
        echo -e "${GREEN}✓ ESLint completed${NC}"
    else
        echo -e "${YELLOW}⚠ ESLint not installed (skip)${NC}"
    fi
    echo ""
fi

echo -e "${GREEN}✅ All security checks passed!${NC}"

