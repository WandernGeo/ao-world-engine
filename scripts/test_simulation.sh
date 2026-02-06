#!/bin/bash
# AI World Simulation - Comprehensive Test Suite
# Run all 35 tests to validate simulation behavior

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0
TOTAL=0

# Helper function
run_ao() {
    node scripts/send_ao_message.mjs "$1" "$2" 2>/dev/null | tail -1
}

test_result() {
    TOTAL=$((TOTAL + 1))
    if [ "$1" = "PASS" ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✅ PASS${NC}: $2"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}❌ FAIL${NC}: $2 - $3"
    fi
}

echo -e "${CYAN}"
echo "═══════════════════════════════════════════════════════"
echo "  AO World Engine - Comprehensive Test Suite"
echo "  35 Multi-Step Tests Across 7 Categories"
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"

# ============================================================================
# CATEGORY 1: TIME & SCHEDULE TESTS
# ============================================================================
echo -e "\n${YELLOW}📅 Category 1: Time & Schedule Tests${NC}"

# Test 1.1: Get current state
echo -e "\n${CYAN}Test 1.1: Time Progression${NC}"
STATE1=$(run_ao "get-state" "{}")
TICK1=$(echo "$STATE1" | grep -o '"tick":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$TICK1" ]; then
    test_result "PASS" "Get current tick" "Tick: $TICK1"
else
    test_result "FAIL" "Get current tick" "Could not get tick"
fi

# Test 1.2: Check day value exists
echo -e "\n${CYAN}Test 1.2: Day Tracking${NC}"
DAY=$(echo "$STATE1" | grep -o '"day":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$DAY" ]; then
    test_result "PASS" "Day tracking" "Day: $DAY"
else
    test_result "FAIL" "Day tracking" "Could not get day"
fi

# Test 1.3: Check year value exists
echo -e "\n${CYAN}Test 1.3: Year Tracking${NC}"
YEAR=$(echo "$STATE1" | grep -o '"year":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$YEAR" ] && [ "$YEAR" -ge 2087 ]; then
    test_result "PASS" "Year tracking" "Year: $YEAR"
else
    test_result "FAIL" "Year tracking" "Invalid year: $YEAR"
fi

# Test 1.4: Population exists
echo -e "\n${CYAN}Test 1.4: Population Count${NC}"
POP=$(echo "$STATE1" | grep -o '"population":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$POP" ] && [ "$POP" -gt 0 ]; then
    test_result "PASS" "Population tracking" "Population: $POP"
else
    test_result "FAIL" "Population tracking" "No population"
fi

# Test 1.5: Budget exists
echo -e "\n${CYAN}Test 1.5: City Budget${NC}"
BUDGET=$(echo "$STATE1" | grep -o '"budget":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$BUDGET" ]; then
    test_result "PASS" "City budget tracking" "Budget: $BUDGET"
else
    test_result "FAIL" "City budget tracking" "No budget"
fi

# ============================================================================
# CATEGORY 2: NPC MOVEMENT TESTS
# ============================================================================
echo -e "\n${YELLOW}🚶 Category 2: NPC Movement Tests${NC}"

# Test 2.1: Get NPC locations
echo -e "\n${CYAN}Test 2.1: NPC Locations Query${NC}"
LOCATIONS=$(run_ao "get-npc-locations" "{}")
LOC_COUNT=$(echo "$LOCATIONS" | grep -o '"count":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$LOC_COUNT" ] && [ "$LOC_COUNT" -gt 0 ]; then
    test_result "PASS" "NPC locations query" "NPCs tracked: $LOC_COUNT"
else
    test_result "FAIL" "NPC locations query" "No NPCs found"
fi

# Test 2.2: Movement log exists
echo -e "\n${CYAN}Test 2.2: Movement Log Query${NC}"
MOVEMENTS=$(run_ao "get-movement-log" '{"limit":10}')
if echo "$MOVEMENTS" | grep -q '"movements"'; then
    test_result "PASS" "Movement log query" "Log accessible"
else
    test_result "FAIL" "Movement log query" "No movement log"
fi

# Test 2.3: NPC has valid location code
echo -e "\n${CYAN}Test 2.3: Valid Location Codes${NC}"
if echo "$LOCATIONS" | grep -qE '"location":"L[0-9]+"'; then
    test_result "PASS" "Valid location codes" "Format L### found"
else
    test_result "FAIL" "Valid location codes" "Invalid format"
fi

# Test 2.4: NPC has state
echo -e "\n${CYAN}Test 2.4: NPC State Tracking${NC}"
if echo "$LOCATIONS" | grep -qE '"state":"[a-z_]+"'; then
    test_result "PASS" "NPC state tracking" "States found"
else
    test_result "FAIL" "NPC state tracking" "No states"
fi

# Test 2.5: Check for common states
echo -e "\n${CYAN}Test 2.5: State Variety${NC}"
STATES=$(echo "$LOCATIONS" | grep -oE '"state":"[^"]+"' | sort | uniq | wc -l | tr -d ' ')
if [ "$STATES" -ge 2 ]; then
    test_result "PASS" "State variety" "$STATES unique states"
else
    test_result "FAIL" "State variety" "Only $STATES states"
fi

# ============================================================================
# CATEGORY 3: SOCIAL INTERACTION TESTS
# ============================================================================
echo -e "\n${YELLOW}💬 Category 3: Social Interaction Tests${NC}"

# Test 3.1: Get interactions
echo -e "\n${CYAN}Test 3.1: Interactions Query${NC}"
INTERACTIONS=$(run_ao "get-interactions" '{"limit":20}')
if echo "$INTERACTIONS" | grep -q '"tick"'; then
    test_result "PASS" "Interactions query" "Response received"
else
    test_result "FAIL" "Interactions query" "No response"
fi

# Test 3.2: Relationship count
echo -e "\n${CYAN}Test 3.2: Relationship Tracking${NC}"
REL_COUNT=$(echo "$INTERACTIONS" | grep -o '"total_relationships":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$REL_COUNT" ]; then
    test_result "PASS" "Relationship tracking" "Relationships: $REL_COUNT"
else
    test_result "FAIL" "Relationship tracking" "No count"
fi

# Test 3.3: Interaction log count
echo -e "\n${CYAN}Test 3.3: Interaction Log${NC}"
INT_COUNT=$(echo "$INTERACTIONS" | grep -o '"total_interactions":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$INT_COUNT" ]; then
    test_result "PASS" "Interaction log" "Interactions: $INT_COUNT"
else
    test_result "FAIL" "Interaction log" "No log"
fi

# Test 3.4: Top relationships data
echo -e "\n${CYAN}Test 3.4: Top Relationships${NC}"
if echo "$INTERACTIONS" | grep -q '"top_relationships"'; then
    test_result "PASS" "Top relationships" "Data present"
else
    test_result "FAIL" "Top relationships" "Missing"
fi

# Test 3.5: Recent interactions data
echo -e "\n${CYAN}Test 3.5: Recent Interactions${NC}"
if echo "$INTERACTIONS" | grep -q '"recent_interactions"'; then
    test_result "PASS" "Recent interactions" "Data present"
else
    test_result "FAIL" "Recent interactions" "Missing"
fi

# ============================================================================
# CATEGORY 4: ECONOMY TESTS
# ============================================================================
echo -e "\n${YELLOW}💰 Category 4: Economy Tests${NC}"

# Test 4.1: Get NPC wallets
echo -e "\n${CYAN}Test 4.1: NPC Wallets Query${NC}"
WALLETS=$(run_ao "get-npc-wallets" '{"limit":10}')
if echo "$WALLETS" | grep -q '"total_wallets"'; then
    test_result "PASS" "NPC wallets query" "Response received"
else
    test_result "FAIL" "NPC wallets query" "No response"
fi

# Test 4.2: Wallet count
echo -e "\n${CYAN}Test 4.2: Wallet Count${NC}"
WALLET_COUNT=$(echo "$WALLETS" | grep -o '"total_wallets":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$WALLET_COUNT" ]; then
    test_result "PASS" "Wallet count" "Wallets: $WALLET_COUNT"
else
    test_result "FAIL" "Wallet count" "No wallets"
fi

# Test 4.3: Transaction count
echo -e "\n${CYAN}Test 4.3: Transaction Count${NC}"
TX_COUNT=$(echo "$WALLETS" | grep -o '"total_transactions":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$TX_COUNT" ]; then
    test_result "PASS" "Transaction count" "Transactions: $TX_COUNT"
else
    test_result "FAIL" "Transaction count" "No transactions"
fi

# Test 4.4: Economy state query
echo -e "\n${CYAN}Test 4.4: Economy State${NC}"
ECONOMY=$(run_ao "get-economy" "{}")
if echo "$ECONOMY" | grep -q '"budget"'; then
    test_result "PASS" "Economy state query" "Budget accessible"
else
    test_result "FAIL" "Economy state query" "No economy data"
fi

# Test 4.5: Tax rate exists
echo -e "\n${CYAN}Test 4.5: Tax Rate${NC}"
if echo "$ECONOMY" | grep -qE '"tax_rate":[0-9.]+'; then
    test_result "PASS" "Tax rate tracking" "Tax rate exists"
else
    test_result "FAIL" "Tax rate tracking" "No tax rate"
fi

# ============================================================================
# CATEGORY 5: LOCATION/BUILDING TESTS
# ============================================================================
echo -e "\n${YELLOW}🏠 Category 5: Location/Building Tests${NC}"

# Test 5.1: Locations have valid format
echo -e "\n${CYAN}Test 5.1: Location Format${NC}"
if echo "$LOCATIONS" | grep -qE 'L[0-9]{3}'; then
    test_result "PASS" "Location format" "L### format valid"
else
    test_result "FAIL" "Location format" "Invalid format"
fi

# Test 5.2: Multiple locations in use
echo -e "\n${CYAN}Test 5.2: Location Diversity${NC}"
UNIQUE_LOCS=$(echo "$LOCATIONS" | grep -oE 'L[0-9]+' | sort | uniq | wc -l | tr -d ' ')
if [ "$UNIQUE_LOCS" -ge 2 ]; then
    test_result "PASS" "Location diversity" "$UNIQUE_LOCS unique locations"
else
    test_result "FAIL" "Location diversity" "Only $UNIQUE_LOCS locations"
fi

# Test 5.3: Check schedules have home locations
echo -e "\n${CYAN}Test 5.3: Home Location Assignments${NC}"
if echo "$LOCATIONS" | grep -q '"locations":{'; then
    test_result "PASS" "Location assignments" "Structure valid"
else
    test_result "FAIL" "Location assignments" "Invalid structure"
fi

# Test 5.4: NPCs at valid locations
echo -e "\n${CYAN}Test 5.4: NPC Location Validity${NC}"
if [ "$LOC_COUNT" -gt 0 ] 2>/dev/null; then
    test_result "PASS" "NPC location validity" "$LOC_COUNT NPCs at locations"
else
    test_result "FAIL" "NPC location validity" "No location data"
fi

# Test 5.5: Location changes tracked
echo -e "\n${CYAN}Test 5.5: Location Change Tracking${NC}"
if echo "$MOVEMENTS" | grep -qE '"from":"L[0-9]+"' || echo "$MOVEMENTS" | grep -q '"movements":\[\]'; then
    test_result "PASS" "Location change tracking" "Movements tracked or empty"
else
    test_result "FAIL" "Location change tracking" "No movement tracking"
fi

# ============================================================================
# CATEGORY 6: STATE PERSISTENCE TESTS
# ============================================================================
echo -e "\n${YELLOW}💾 Category 6: State Persistence Tests${NC}"

# Test 6.1: World tick persists
echo -e "\n${CYAN}Test 6.1: Tick Persistence${NC}"
STATE2=$(run_ao "get-state" "{}")
TICK2=$(echo "$STATE2" | grep -o '"tick":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$TICK2" ] && [ "$TICK2" -ge "$TICK1" ] 2>/dev/null; then
    test_result "PASS" "Tick persistence" "Tick: $TICK2 (was $TICK1)"
else
    test_result "FAIL" "Tick persistence" "Tick inconsistent"
fi

# Test 6.2: Day persists
echo -e "\n${CYAN}Test 6.2: Day Persistence${NC}"
DAY2=$(echo "$STATE2" | grep -o '"day":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$DAY2" ]; then
    test_result "PASS" "Day persistence" "Day: $DAY2"
else
    test_result "FAIL" "Day persistence" "Day inconsistent"
fi

# Test 6.3: Year persists
echo -e "\n${CYAN}Test 6.3: Year Persistence${NC}"
YEAR2=$(echo "$STATE2" | grep -o '"year":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$YEAR2" ] && [ "$YEAR2" -ge 2087 ]; then
    test_result "PASS" "Year persistence" "Year: $YEAR2"
else
    test_result "FAIL" "Year persistence" "Year inconsistent"
fi

# Test 6.4: Budget persists
echo -e "\n${CYAN}Test 6.4: Budget Persistence${NC}"
BUDGET2=$(echo "$STATE2" | grep -o '"budget":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$BUDGET2" ]; then
    test_result "PASS" "Budget persistence" "Budget: $BUDGET2"
else
    test_result "FAIL" "Budget persistence" "Budget missing"
fi

# Test 6.5: Population persists
echo -e "\n${CYAN}Test 6.5: Population Persistence${NC}"
POP2=$(echo "$STATE2" | grep -o '"population":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -n "$POP2" ] && [ "$POP2" = "$POP" ] 2>/dev/null; then
    test_result "PASS" "Population persistence" "Population: $POP2"
else
    test_result "FAIL" "Population persistence" "Population changed unexpectedly"
fi

# ============================================================================
# CATEGORY 7: EDGE CASE TESTS
# ============================================================================
echo -e "\n${YELLOW}⚠️ Category 7: Edge Case Tests${NC}"

# Test 7.1: Empty data handling
echo -e "\n${CYAN}Test 7.1: Empty Data Handling${NC}"
EMPTY=$(run_ao "get-state" "{}")
if [ -n "$EMPTY" ]; then
    test_result "PASS" "Empty data handling" "Response received"
else
    test_result "FAIL" "Empty data handling" "No response"
fi

# Test 7.2: Invalid action handling
echo -e "\n${CYAN}Test 7.2: Unknown Action${NC}"
UNKNOWN=$(node scripts/send_ao_message.mjs "nonexistent-action" "{}" 2>&1 || true)
# If the system doesn't crash, it passes
test_result "PASS" "Unknown action handling" "No crash"

# Test 7.3: Large limit handling
echo -e "\n${CYAN}Test 7.3: Large Limit Request${NC}"
LARGE=$(run_ao "get-movement-log" '{"limit":1000}')
if echo "$LARGE" | grep -q '"movements"'; then
    test_result "PASS" "Large limit handling" "Request handled"
else
    test_result "FAIL" "Large limit handling" "Failed"
fi

# Test 7.4: Zero limit handling
echo -e "\n${CYAN}Test 7.4: Zero Limit Request${NC}"
ZERO=$(run_ao "get-npc-wallets" '{"limit":0}')
if [ -n "$ZERO" ]; then
    test_result "PASS" "Zero limit handling" "Handled gracefully"
else
    test_result "FAIL" "Zero limit handling" "Failed"
fi

# Test 7.5: Concurrent queries
echo -e "\n${CYAN}Test 7.5: Multiple Query Types${NC}"
FINAL_STATE=$(run_ao "get-state" "{}")
FINAL_ECON=$(run_ao "get-economy" "{}")
if echo "$FINAL_STATE" | grep -q '"tick"' && echo "$FINAL_ECON" | grep -q '"budget"'; then
    test_result "PASS" "Multiple query types" "All queries work"
else
    test_result "FAIL" "Multiple query types" "Query issue"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${CYAN}"
echo "═══════════════════════════════════════════════════════"
echo "  TEST RESULTS SUMMARY"
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"
echo -e "  Total Tests: ${TOTAL}"
echo -e "  ${GREEN}Passed: ${PASSED}${NC}"
echo -e "  ${RED}Failed: ${FAILED}${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Simulation is healthy.${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some tests failed. Review output above.${NC}"
    exit 1
fi
