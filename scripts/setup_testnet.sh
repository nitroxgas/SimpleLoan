#!/bin/bash
# Setup Liquid Testnet Environment for Fantasma Protocol
# Creates test assets, initializes reserves, and funds test accounts

set -e  # Exit on error

echo "========================================"
echo "Fantasma Protocol Testnet Setup"
echo "========================================"
echo ""

# Configuration
NETWORK="liquidtestnet"
ELEMENTS_CLI="elements-cli -chain=liquidtestnet"
BACKEND_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v elements-cli &> /dev/null; then
    echo -e "${RED}Error: elements-cli not found${NC}"
    echo "Install Elements Core from: https://elementsproject.org/"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check if Elements node is running
echo "Checking Elements node connection..."
if ! $ELEMENTS_CLI getblockchaininfo &> /dev/null; then
    echo -e "${YELLOW}Warning: Cannot connect to Elements node${NC}"
    echo "Starting elementsd..."
    elementsd -chain=liquidtestnet -daemon -fallbackfee=0.00001
    echo "Waiting for node to start..."
    sleep 10
fi

CHAIN_INFO=$($ELEMENTS_CLI getblockchaininfo)
BLOCKS=$(echo $CHAIN_INFO | grep -o '"blocks": [0-9]*' | awk '{print $2}')
echo -e "${GREEN}✓ Connected to Liquid testnet (block height: $BLOCKS)${NC}"
echo ""

# Create or load wallet
echo "Setting up wallet..."
WALLET_NAME="fantasma_testnet"

if $ELEMENTS_CLI listwallets | grep -q "$WALLET_NAME"; then
    echo "Wallet '$WALLET_NAME' already loaded"
else
    if $ELEMENTS_CLI listwalletdir | grep -q "$WALLET_NAME"; then
        echo "Loading existing wallet '$WALLET_NAME'..."
        $ELEMENTS_CLI loadwallet "$WALLET_NAME"
    else
        echo "Creating new wallet '$WALLET_NAME'..."
        $ELEMENTS_CLI createwallet "$WALLET_NAME"
    fi
fi

# Get wallet address and balance
WALLET_ADDRESS=$($ELEMENTS_CLI getnewaddress)
LBTC_BALANCE=$($ELEMENTS_CLI getbalance)

echo -e "${GREEN}✓ Wallet ready${NC}"
echo "  Name: $WALLET_NAME"
echo "  Address: $WALLET_ADDRESS"
echo "  LBTC Balance: $LBTC_BALANCE"
echo ""

# Fund wallet if needed
if (( $(echo "$LBTC_BALANCE < 1.0" | bc -l) )); then
    echo -e "${YELLOW}Low LBTC balance. Requesting from faucet...${NC}"
    echo "Faucet URL: https://liquidtestnet.com/faucet?address=$WALLET_ADDRESS&action=lbtc"
    
    # Try to fund from faucet
    FAUCET_RESPONSE=$(curl -s "https://liquidtestnet.com/faucet?address=$WALLET_ADDRESS&action=lbtc" || echo "")
    
    if [ -n "$FAUCET_RESPONSE" ]; then
        echo -e "${GREEN}✓ Faucet request sent${NC}"
        echo "Waiting for confirmation..."
        sleep 30
        
        LBTC_BALANCE=$($ELEMENTS_CLI getbalance)
        echo "New balance: $LBTC_BALANCE LBTC"
    else
        echo -e "${YELLOW}Faucet request failed. Please fund manually:${NC}"
        echo "  1. Visit: https://liquidtestnet.com/faucet"
        echo "  2. Enter address: $WALLET_ADDRESS"
        echo "  3. Click 'Get LBTC'"
        echo ""
        read -p "Press Enter after funding..."
    fi
fi

echo ""

# Create test assets (BTC and USDT representations)
echo "Creating test assets..."

# Check if assets already exist in config
if [ -f ".env" ] && grep -q "BTC_ASSET_ID" .env; then
    echo "Assets already configured in .env"
    source .env
else
    echo "Issuing new test assets..."
    
    # Issue test BTC asset (reissuable)
    echo "  Issuing test BTC..."
    BTC_ASSET_RESULT=$($ELEMENTS_CLI issueasset 1000 0 true)
    BTC_ASSET_ID=$(echo $BTC_ASSET_RESULT | grep -o '"asset":"[^"]*"' | head -1 | cut -d'"' -f4)
    BTC_TOKEN=$(echo $BTC_ASSET_RESULT | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    echo -e "${GREEN}✓ Test BTC issued${NC}"
    echo "  Asset ID: $BTC_ASSET_ID"
    echo "  Token: $BTC_TOKEN"
    
    # Issue test USDT asset (reissuable)
    echo "  Issuing test USDT..."
    USDT_ASSET_RESULT=$($ELEMENTS_CLI issueasset 1000000 0 true)
    USDT_ASSET_ID=$(echo $USDT_ASSET_RESULT | grep -o '"asset":"[^"]*"' | head -1 | cut -d'"' -f4)
    USDT_TOKEN=$(echo $USDT_ASSET_RESULT | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    echo -e "${GREEN}✓ Test USDT issued${NC}"
    echo "  Asset ID: $USDT_ASSET_ID"
    echo "  Token: $USDT_TOKEN"
    
    # Save to .env
    cat > .env << EOF
# Fantasma Protocol Testnet Configuration
# Generated on $(date)

# Network
NETWORK=liquidtestnet
ELEMENTS_RPC_URL=http://localhost:7041
ELEMENTS_RPC_USER=user
ELEMENTS_RPC_PASSWORD=password

# Test Assets
BTC_ASSET_ID=$BTC_ASSET_ID
BTC_TOKEN=$BTC_TOKEN
USDT_ASSET_ID=$USDT_ASSET_ID
USDT_TOKEN=$USDT_TOKEN

# Wallet
WALLET_NAME=$WALLET_NAME
WALLET_ADDRESS=$WALLET_ADDRESS

# Backend
BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite+aiosqlite:///./fantasma.db

# Frontend
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_NETWORK=liquidtestnet
EOF
    
    echo -e "${GREEN}✓ Configuration saved to .env${NC}"
fi

echo ""

# Initialize database
echo "Initializing database..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || echo "Activate venv manually"

if [ ! -f "fantasma.db" ]; then
    echo "Running database migrations..."
    alembic upgrade head
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo "Database already exists"
fi

cd ..
echo ""

# Create initial reserves (via API)
echo "Creating initial reserves..."

# Wait for backend to be running
if ! curl -s $BACKEND_URL/health &> /dev/null; then
    echo -e "${YELLOW}Warning: Backend not running${NC}"
    echo "Start backend with: cd backend && uvicorn src.main:app --reload"
    echo ""
    echo "After starting backend, run this command to create reserves:"
    echo "  curl -X POST $BACKEND_URL/api/v1/admin/initialize-reserves"
else
    # Initialize reserves
    INIT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/admin/initialize-reserves" \
        -H "Content-Type: application/json" \
        -d "{\"btc_asset_id\": \"$BTC_ASSET_ID\", \"usdt_asset_id\": \"$USDT_ASSET_ID\"}" || echo "")
    
    if [ -n "$INIT_RESPONSE" ]; then
        echo -e "${GREEN}✓ Reserves initialized${NC}"
    else
        echo -e "${YELLOW}Reserve initialization pending (start backend first)${NC}"
    fi
fi

echo ""

# Summary
echo "========================================"
echo "Testnet Setup Complete!"
echo "========================================"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Network: Liquid Testnet"
echo "  Wallet: $WALLET_ADDRESS"
echo "  LBTC Balance: $LBTC_BALANCE"
echo "  Test BTC Asset: ${BTC_ASSET_ID:0:16}..."
echo "  Test USDT Asset: ${USDT_ASSET_ID:0:16}..."
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Start backend:"
echo "     cd backend && uvicorn src.main:app --reload"
echo ""
echo "  2. Start frontend:"
echo "     cd frontend && npm start"
echo ""
echo "  3. Open browser:"
echo "     http://localhost:3000"
echo ""
echo "  4. Use test tokens:"
echo "     ./scripts/mint_test_tokens.sh"
echo ""
echo -e "${GREEN}Resources:${NC}"
echo "  • Testnet Explorer: https://blockstream.info/liquidtestnet/"
echo "  • Testnet Faucet: https://liquidtestnet.com/faucet"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
