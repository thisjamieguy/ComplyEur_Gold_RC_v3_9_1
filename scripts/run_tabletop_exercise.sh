#!/bin/bash
# Incident Response Tabletop Exercise Runner
# Phase 4: Network & Infrastructure Security

set -e

SCENARIO="$1"
LOG_DIR="./logs/incident_response"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

if [ -z "$SCENARIO" ]; then
    echo -e "${BLUE}Available Scenarios:${NC}"
    echo "  1. sql_injection"
    echo "  2. ddos_attack"
    echo "  3. unauthorized_access"
    echo "  4. data_breach"
    echo "  5. backup_corruption"
    echo ""
    echo "Usage: $0 <scenario_number_or_name>"
    exit 1
fi

# Map scenario numbers to names
case "$SCENARIO" in
    1|sql_injection)
        SCENARIO_NAME="SQL Injection Attempt"
        SCENARIO_FILE="sql_injection"
        ;;
    2|ddos_attack)
        SCENARIO_NAME="DDoS Attack on Login"
        SCENARIO_FILE="ddos_attack"
        ;;
    3|unauthorized_access)
        SCENARIO_NAME="Unauthorized Admin Access"
        SCENARIO_FILE="unauthorized_access"
        ;;
    4|data_breach)
        SCENARIO_NAME="Suspected Data Breach"
        SCENARIO_FILE="data_breach"
        ;;
    5|backup_corruption)
        SCENARIO_NAME="Backup Corruption Detected"
        SCENARIO_FILE="backup_corruption"
        ;;
    *)
        echo -e "${RED}Unknown scenario: $SCENARIO${NC}"
        exit 1
        ;;
esac

LOG_FILE="$LOG_DIR/tabletop_${SCENARIO_FILE}_${TIMESTAMP}.md"

cat > "$LOG_FILE" << EOF
# Tabletop Exercise Log
**Scenario:** $SCENARIO_NAME
**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Exercise ID:** EX-$(date '+%Y%m%d')-$(echo $SCENARIO_FILE | tr '[:lower:]' '[:upper:]')

---

## Scenario: $SCENARIO_NAME

### Participants
- [ ] AppSec Lead
- [ ] Compliance Officer
- [ ] DevOps Lead
- [ ] Incident Responder

---

## Exercise Timeline

### Detection
**Time:** [Timestamp]
**Method:** [Automated/Manual]
**Initial Assessment:**
- [ ] Alert received
- [ ] Severity classified
- [ ] Team notified

### Response Actions
**Time:** [Timestamp]
- [ ] Containment initiated
- [ ] Evidence preserved
- [ ] Logs reviewed
- [ ] Backup verified
- [ ] Access reviewed

### Resolution
**Time:** [Timestamp]
- [ ] Incident contained
- [ ] Root cause identified
- [ ] Fixes implemented
- [ ] Monitoring enhanced

---

## Lessons Learned

### What Went Well
- 

### Areas for Improvement
- 

### Action Items
- [ ] 
- [ ] 
- [ ] 

---

## Next Steps
- [ ] Update incident response plan
- [ ] Improve detection mechanisms
- [ ] Update security controls
- [ ] Schedule follow-up review

---

**Exercise Completed:** [Yes/No]
**Sign-off:** 
- AppSec Lead: _________________ Date: _______
- Compliance Officer: _________________ Date: _______

EOF

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Tabletop Exercise: $SCENARIO_NAME${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""
echo -e "Log file: ${GREEN}$LOG_FILE${NC}"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "1. Review scenario in: infra/incident_response.md"
echo "2. Document response actions in log file"
echo "3. Complete all checklist items"
echo "4. Document lessons learned"
echo ""
echo -e "${BLUE}Opening log file for editing...${NC}"

# Try to open in editor (or just display)
if command -v nano &> /dev/null; then
    nano "$LOG_FILE"
elif command -v vim &> /dev/null; then
    vim "$LOG_FILE"
else
    echo ""
    echo -e "${YELLOW}Log file created. Edit manually:${NC}"
    echo "  $LOG_FILE"
fi

echo ""
echo -e "${GREEN}✅ Tabletop exercise log created${NC}"

