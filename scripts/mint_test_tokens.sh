#!/bin/bash
# Mint Test Tokens for Fantasma Protocol Testing
# Issues additional test BTC and USDT to wallet for protocol testing

set -e  # Exit on error

echo "========================================"
echo "Fantasma Protocol - Mint Test Tokens"
echo "========================================"
echo ""

# Configuration
ELEMENTS_CLI="elements-cli -chain=liquidtestnet"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load configuration
if [ ! -f ".env" ]; then
    echo "Error: .env not found. Run ./scripts/setup_testnet.sh first"
    exit 1
fi

source .env

# Check Elements connection
if ! $ELEMENTS_CLI getblockchaininfo &> /dev/null; then
    echo "Error: Cannot connect to Elements node"
    echo "Make sure elementsd is running with: elementsd -chain=liquidtestnet -daemon"
    exit 1
fi

echo "Current wallet: $WALLET_ADDRESS"
echo ""

# Show current balances
echo "Current balances:"
BTC_BALANCE=$($ELEMENTS_CLI getbalance "*" 1 false "$BTC_ASSET_ID" 2>/dev/null || echo "0")
USDT_BALANCE=$($ELEMENTS_CLI getbalance "*" 1 false "$USDT_ASSET_ID" 2>/dev/null || echo "0")
LBTC_BALANCE=$($ELEMENTS_CLI getbalance)

echo "  LBTC: $LBTC_BALANCE"
echo "  Test BTC: $BTC_BALANCE"
echo "  Test USDT: $USDT_BALANCE"
echo ""

# Mint more test BTC
echo "Minting test BTC..."
BTC_AMOUNT=${1:-10.0}  # Default 10 BTC
REISSUE_RESULT=$($ELEMENTS_CLI reissueasset "$BTC_ASSET_ID" "$BTC_AMOUNT")
REISSUE_TX=$(echo $REISSUE_RESULT | grep -o '"txid":"[^"]*"' | cut -d'"' -f4)

echo -e "${GREEN}✓ Minted $BTC_AMOUNT test BTC${NC}"
echo "  Transaction: $REISSUE_TX"
echo ""

# Mint more test USDT
echo "Minting test USDT..."
USDT_AMOUNT=${2:-100000.0}  # Default 100k USDT
REISSUE_RESULT=$($ELEMENTS_CLI reissueasset "$USDT_ASSET_ID" "$USDT_AMOUNT")
REISSUE_TX=$(echo $REISSUE_RESULT | grep -o '"txid":"[^"]*"' | cut -d'"' -f4)

echo -e "${GREEN}✓ Minted $USDT_AMOUNT test USDT${NC}"
echo "  Transaction: $REISSUE_TX"
echo ""

# Wait for confirmation
echo "Waiting for confirmations..."
sleep 5

# Show new balances
echo "New balances:"
BTC_BALANCE=$($ELEMENTS_CLI getbalance "*" 1 false "$BTC_ASSET_ID" 2>/dev/null || echo "0")
USDT_BALANCE=$($ELEMENTS_CLI getbalance "*" 1 false "$USDT_ASSET_ID" 2>/dev/null || echo "0")

echo "  Test BTC: $BTC_BALANCE"
echo "  Test USDT: $USDT_BALANCE"
echo ""

echo -e "${GREEN}Done! You can now use these tokens in Fantasma Protocol${NC}"
echo ""
echo "Usage examples:"
echo "  # Mint custom amounts"
echo "  ./scripts/mint_test_tokens.sh 5.0 50000.0"
echo ""
echo "  # Supply to protocol"
echo "  curl -X POST http://localhost:8000/api/v1/supply \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_address\": \"$WALLET_ADDRESS\", \"asset_id\": \"$BTC_ASSET_ID\", \"amount\": 100000000}'"
echo ""
