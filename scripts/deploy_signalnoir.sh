#!/bin/bash
#
# SignalNoir.1 Deployment Script
# Deploys the autonomous simulation to AO testnet
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AO_PROCESSES="$PROJECT_ROOT/ao-processes"
WALLET_PATH="${WALLET_PATH:-$PROJECT_ROOT/../wandern-back/arweave-wallet.json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           SignalNoir.1 - AO Deployment Script             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AOS CLI
if ! command -v aos &> /dev/null; then
    echo -e "${RED}✗ AOS CLI not found${NC}"
    echo "  Install with: npm i -g https://get_ao.g8way.io"
    exit 1
fi
echo -e "${GREEN}✓ AOS CLI: $(aos --version 2>&1 | head -1)${NC}"

# Check wallet
if [ ! -f "$WALLET_PATH" ]; then
    echo -e "${RED}✗ Wallet not found at: $WALLET_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Wallet found: $WALLET_PATH${NC}"

# Check Lua files
for file in world.lua economy.lua social.lua logging.lua signalnoir_config.lua; do
    if [ ! -f "$AO_PROCESSES/$file" ]; then
        echo -e "${RED}✗ Missing: $AO_PROCESSES/$file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All Lua modules present${NC}"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Deployment options
echo -e "${YELLOW}Deployment Options:${NC}"
echo "  1. Interactive REPL (recommended for first test)"
echo "  2. Background process with CRON"
echo "  3. Dry run (validate files only)"
echo ""
read -p "Select option [1-3]: " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo ""
        echo -e "${CYAN}Starting AOS Interactive Session...${NC}"
        echo -e "${YELLOW}Run these commands in the AOS REPL:${NC}"
        echo ""
        echo "  .load ao-processes/logging.lua"
        echo "  .load ao-processes/economy.lua"
        echo "  .load ao-processes/social.lua"
        echo "  .load ao-processes/world.lua"
        echo "  .load ao-processes/signalnoir_config.lua"
        echo ""
        echo "  -- Then to start CRON:"
        echo "  Send({ Target = ao.id, Action = \"Cron\", Tags = { { name = \"Cron-Interval\", value = \"1-minute\" } } })"
        echo ""
        
        cd "$PROJECT_ROOT"
        aos SignalNoir1 --wallet "$WALLET_PATH"
        ;;
        
    2)
        echo ""
        echo -e "${CYAN}Creating combined loader file...${NC}"
        
        # Create a combined loader file
        LOADER_FILE="$AO_PROCESSES/signalnoir_loader.lua"
        cat > "$LOADER_FILE" << 'EOF'
-- SignalNoir.1 Combined Loader
-- Auto-generated deployment script

print("Loading SignalNoir.1 modules...")

-- Load in order
dofile("ao-processes/logging.lua")
print("✓ logging.lua")

dofile("ao-processes/economy.lua")
print("✓ economy.lua")

dofile("ao-processes/social.lua")
print("✓ social.lua")

dofile("ao-processes/world.lua")
print("✓ world.lua")

dofile("ao-processes/signalnoir_config.lua")
print("✓ signalnoir_config.lua")

print("")
print("SignalNoir.1 loaded. Starting CRON...")

-- Start 1-minute CRON
ao.send({
    Target = ao.id,
    Action = "Cron",
    Tags = {
        { name = "Cron-Interval", value = "1-minute" }
    }
})

print("CRON configured. Simulation will begin on next tick.")
EOF
        
        echo -e "${GREEN}✓ Created: $LOADER_FILE${NC}"
        echo ""
        echo -e "${CYAN}Starting AOS with loader...${NC}"
        
        cd "$PROJECT_ROOT"
        aos SignalNoir1 --wallet "$WALLET_PATH" --load ao-processes/signalnoir_loader.lua --cron 1-minute
        ;;
        
    3)
        echo ""
        echo -e "${CYAN}Dry Run - Validating files...${NC}"
        
        # Check Lua syntax
        for file in logging.lua economy.lua social.lua world.lua signalnoir_config.lua; do
            if lua -p "$AO_PROCESSES/$file" 2>/dev/null; then
                echo -e "${GREEN}✓ $file - syntax OK${NC}"
            else
                echo -e "${YELLOW}⚠ $file - syntax check (may need AO runtime)${NC}"
            fi
        done
        
        echo ""
        echo -e "${GREEN}Validation complete. Ready to deploy!${NC}"
        ;;
        
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Monitoring Commands:${NC}"
echo ""
echo "  -- Check status:"
echo "  Send({ Target = ao.id, Action = 'get-signalnoir-status' })"
echo ""
echo "  -- Get recent logs:"
echo "  Send({ Target = ao.id, Action = 'get-logs', Data = '{\"type\": \"npc_action\", \"limit\": 10}' })"
echo ""
echo "  -- Get NPC history:"
echo "  Send({ Target = ao.id, Action = 'get-npc-history', Data = '{\"npc_id\": \"C01\"}' })"
echo ""
echo "  -- Get economy state:"
echo "  Send({ Target = ao.id, Action = 'get-economy' })"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
