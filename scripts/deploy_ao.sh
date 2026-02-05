#!/bin/bash
# AO World Engine - Deployment Script
# 
# This script helps deploy the simulation to AO testnet.
# 
# Prerequisites:
#   - aos CLI installed: npm install -g aos
#   - Arweave wallet (wallet.json) in current directory
#   - Node.js 18+
#
# Usage:
#   ./deploy_ao.sh [testnet|mainnet]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NETWORK=${1:-testnet}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AO_PROCESSES_DIR="$SCRIPT_DIR/../ao-processes"
WALLET_PATH="${WALLET_PATH:-/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AO World Engine - Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aos &> /dev/null; then
    echo -e "${RED}Error: aos CLI not found${NC}"
    echo "Install with: npm install -g aos"
    exit 1
fi
echo -e "${GREEN}✓ aos CLI found${NC}"

if [ ! -f "$WALLET_PATH" ]; then
    echo -e "${RED}Error: Wallet not found at $WALLET_PATH${NC}"
    echo "Set WALLET_PATH environment variable or place wallet.json in current directory"
    exit 1
fi
echo -e "${GREEN}✓ Wallet found${NC}"

# Check Lua files exist
LUA_FILES=("world.lua" "economy.lua" "social.lua" "district.lua" "ai_oracle.lua" "init_bootstrap.lua")
for file in "${LUA_FILES[@]}"; do
    if [ ! -f "$AO_PROCESSES_DIR/$file" ]; then
        echo -e "${RED}Error: $file not found in ao-processes/${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All Lua modules found${NC}"
echo ""

# Deployment steps
echo -e "${YELLOW}Deployment Steps:${NC}"
echo "1. Upload Lua modules to Arweave"
echo "2. Spawn world process with CRON"
echo "3. Spawn district processes"
echo "4. Register all processes"
echo "5. Initialize simulation"
echo ""

read -p "Continue with deployment to $NETWORK? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting AOS session...${NC}"
echo ""

# Create deployment script for AOS
DEPLOY_SCRIPT=$(cat << 'EOF'
-- AO World Engine Deployment Script
local json = require("json")

print("========================================")
print("  AO World Engine - Deployment")
print("========================================")
print("")

-- Step 1: Load modules
print("Step 1: Loading modules...")

-- Load bootstrap
.load ao-processes/init_bootstrap.lua
print("  ✓ init_bootstrap.lua")

.load ao-processes/world.lua
print("  ✓ world.lua")

-- Step 2: Initialize
print("")
print("Step 2: Initializing world...")
local result = Initialize()
print("  ✓ World initialized")
print("    - Tick: " .. result.world_tick)
print("    - Budget: " .. result.budget .. " GEP")
print("    - Districts: " .. result.districts)
print("    - Population: " .. result.population)

-- Step 3: Display CRON setup instructions
print("")
print("Step 3: CRON Setup")
print("  The world process needs CRON to run autonomously.")
print("  When spawning the process, use these tags:")
print("")
print('  ao.spawn("world-module-txid", {')
print('      Tags = {')
print('          { name = "Cron-Interval", value = "10-minutes" },')
print('          { name = "Cron-Tag-Action", value = "Cron" }')
print('      }')
print('  })')
print("")

print("========================================")
print("  Deployment Complete!")
print("========================================")
print("")
print("Process ID: " .. ao.id)
print("")
print("To test, send a message:")
print('  ao.send({ Target = ao.id, Action = "get-state" })')
print("")
EOF
)

echo "$DEPLOY_SCRIPT" > /tmp/ao_deploy.lua

echo -e "${BLUE}Launching AOS with deployment script...${NC}"
echo ""
echo "Run these commands in the AOS REPL:"
echo ""
echo "  .load $AO_PROCESSES_DIR/init_bootstrap.lua"
echo "  .load $AO_PROCESSES_DIR/world.lua"
echo "  Initialize()"
echo ""

# Launch AOS
aos --wallet "$WALLET_PATH"
