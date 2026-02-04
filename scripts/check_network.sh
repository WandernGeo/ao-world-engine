#!/bin/bash
#
# SignalNoir.1 - Network Status Check and Auto-Retry
# Checks AO network availability and attempts deployment when ready
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WALLET_PATH="${WALLET_PATH:-$PROJECT_ROOT/../wandern-back/arweave-wallet.json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check_network() {
    echo -e "${CYAN}[$(date +%H:%M:%S)] Checking AO network status...${NC}"
    
    # Check gateway
    ARWEAVE_STATUS=$(curl -s --max-time 5 https://arweave.net/info 2>/dev/null | grep -c "height")
    
    if [ "$ARWEAVE_STATUS" = "1" ]; then
        echo -e "${GREEN}  ✓ Arweave gateway: ONLINE${NC}"
    else
        echo -e "${RED}  ✗ Arweave gateway: OFFLINE${NC}"
        return 1
    fi
    
    # Try to spawn a quick test process
    echo -e "${YELLOW}  ⏳ Testing AO connection...${NC}"
    
    RESULT=$(timeout 20 aos --run "return 'test'" --wallet "$WALLET_PATH" 2>&1)
    
    if echo "$RESULT" | grep -q "test"; then
        echo -e "${GREEN}  ✓ AO network: ONLINE${NC}"
        return 0
    elif echo "$RESULT" | grep -q "Error sending message"; then
        echo -e "${RED}  ✗ AO network: CONNECTION ERROR${NC}"
        return 1
    else
        echo -e "${YELLOW}  ⚠ AO network: UNKNOWN STATUS${NC}"
        return 1
    fi
}

deploy_signalnoir() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Starting SignalNoir.1 Deployment${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Load all modules into a single process
    aos SignalNoir1 \
        --wallet "$WALLET_PATH" \
        --cron 1-minute \
        --load ao-processes/logging.lua \
        --load ao-processes/economy.lua \
        --load ao-processes/social.lua \
        --load ao-processes/world.lua \
        --load ao-processes/signalnoir_config.lua
}

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     SignalNoir.1 - Network Check & Deploy                  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we should retry automatically
if [ "$1" = "--auto" ]; then
    MAX_RETRIES=10
    RETRY_INTERVAL=300  # 5 minutes
    
    for i in $(seq 1 $MAX_RETRIES); do
        echo ""
        echo -e "${YELLOW}Attempt $i of $MAX_RETRIES${NC}"
        
        if check_network; then
            echo ""
            echo -e "${GREEN}Network available! Starting deployment...${NC}"
            deploy_signalnoir
            exit 0
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            echo ""
            echo -e "${YELLOW}Retrying in $(($RETRY_INTERVAL / 60)) minutes...${NC}"
            sleep $RETRY_INTERVAL
        fi
    done
    
    echo ""
    echo -e "${RED}Max retries reached. Network still unavailable.${NC}"
    exit 1
else
    # Single check
    if check_network; then
        echo ""
        read -p "Network is available. Deploy now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            deploy_signalnoir
        fi
    else
        echo ""
        echo -e "${YELLOW}Network not available. Options:${NC}"
        echo "  1. Run with --auto to retry every 5 minutes"
        echo "  2. Check https://viewblock.io/arweave for network status"
        echo "  3. Try again later manually"
        echo ""
        echo "Example: $0 --auto"
    fi
fi
