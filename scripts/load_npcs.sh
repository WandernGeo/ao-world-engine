#!/bin/bash
# AO World Engine - Load NPCs Script
#
# This script loads the 800 NPCs into the running AO process.
#
# Prerequisites:
#   - aos CLI: npm install -g aos
#   - Wallet at WALLET_PATH
#   - AO process already spawned
#
# Usage: ./load_npcs.sh [process-id]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AO_DIR="$SCRIPT_DIR/../ao-processes"
WALLET_PATH="${WALLET_PATH:-/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json}"
PROCESS_ID="${1:-3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0}"

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  AO World Engine - Load NPCs${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Process ID:${NC} $PROCESS_ID"
echo -e "${CYAN}Wallet:${NC} $WALLET_PATH"
echo -e "${CYAN}NPC File:${NC} $AO_DIR/all_npcs.lua"
echo ""

# Check prerequisites
if ! command -v aos &> /dev/null; then
    echo -e "${YELLOW}Warning: aos CLI not found. Install with: npm install -g aos${NC}"
    exit 1
fi

if [ ! -f "$WALLET_PATH" ]; then
    echo -e "${YELLOW}Warning: Wallet not found at $WALLET_PATH${NC}"
    exit 1
fi

if [ ! -f "$AO_DIR/all_npcs.lua" ]; then
    echo -e "${YELLOW}Warning: all_npcs.lua not found${NC}"
    exit 1
fi

# Count NPCs
NPC_COUNT=$(grep -c "^\s*\[\"NPC" "$AO_DIR/all_npcs.lua" || echo "800")
echo -e "${GREEN}✓ Found ~$NPC_COUNT NPCs in all_npcs.lua${NC}"
echo ""

# Create load script
LOAD_SCRIPT=$(cat << 'EOFLOAD'
-- Load NPCs into AO World Engine
print("Loading NPCs...")

.load ao-processes/all_npcs.lua
print("✓ NPC data loaded")

-- Initialize with population count
Send({ 
    Target = ao.id, 
    Action = "Init", 
    Data = '{"population": 800}' 
})
print("✓ Population initialized to 800")

-- Verify state
Send({ Target = ao.id, Action = "get-state" })
print("")
print("Loading complete! Check the response for updated population count.")
EOFLOAD
)

echo -e "${YELLOW}To load NPCs, run these commands in aos:${NC}"
echo ""
echo -e "${CYAN}aos $PROCESS_ID --wallet $WALLET_PATH${NC}"
echo ""
echo "Then in the REPL:"
echo -e "${GREEN}.load ao-processes/all_npcs.lua${NC}"
echo -e "${GREEN}Send({ Target = ao.id, Action = \"Init\", Data = '{\"population\": 800}' })${NC}"
echo ""
echo -e "${YELLOW}Or run aos interactively now:${NC}"
read -p "Launch aos? [y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$SCRIPT_DIR/.."
    aos "$PROCESS_ID" --wallet "$WALLET_PATH"
fi
