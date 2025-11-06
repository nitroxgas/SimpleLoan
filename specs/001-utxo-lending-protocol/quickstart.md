# Quickstart Guide: UTXO Lending Protocol

**Feature**: 001-utxo-lending-protocol  
**Date**: 2025-11-06  
**Audience**: Developers setting up local development environment

## Overview

This guide walks through setting up a complete development environment for the UTXO-based lending protocol, including:
- Elements Core (Liquid regtest node)
- Python backend with FastAPI
- React frontend with TypeScript
- SQLite database
- SimplicityHL validator development environment

**Estimated Setup Time**: 30-45 minutes

---

## Prerequisites

### Required Software

- **Python 3.11+**: [python.org/downloads](https://python.org/downloads)
- **Node.js 18+**: [nodejs.org](https://nodejs.org)
- **Elements Core**: [github.com/ElementsProject/elements](https://github.com/ElementsProject/elements)
- **Git**: [git-scm.com](https://git-scm.com)
- **SimplicityHL Compiler**: [github.com/BlockstreamResearch/simplicity](https://github.com/BlockstreamResearch/simplicity)

### Optional Tools

- **Coq**: For formal verification proofs
- **Docker**: For containerized development
- **Postman/Insomnia**: For API testing

---

## Step 1: Clone Repository

```bash
git clone https://github.com/fantasma-protocol/utxo-lending.git
cd utxo-lending
git checkout 001-utxo-lending-protocol
```

---

## Step 2: Setup Elements Core (Liquid Regtest)

### 2.1 Install Elements Core

**Linux/macOS**:
```bash
# Download Elements Core
wget https://github.com/ElementsProject/elements/releases/download/elements-22.1/elements-22.1-x86_64-linux-gnu.tar.gz
tar -xzf elements-22.1-x86_64-linux-gnu.tar.gz
sudo cp elements-22.1/bin/* /usr/local/bin/
```

**Windows**:
Download from [Elements releases](https://github.com/ElementsProject/elements/releases) and add to PATH.

### 2.2 Configure Regtest

Create `~/.elements/elements.conf`:
```ini
# Regtest configuration
regtest=1
daemon=1
server=1

# RPC settings
rpcuser=liquiduser
rpcpassword=liquidpass
rpcport=18884
rpcallowip=127.0.0.1

# Network settings
port=18886
listen=1

# Wallet settings
fallbackfee=0.00001
```

### 2.3 Start Regtest Node

```bash
# Start Elements daemon
elementsd -regtest

# Wait for startup (5-10 seconds)
sleep 10

# Generate initial blocks (need 101 for coinbase maturity)
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass generate 101

# Create wallet
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass createwallet "testwallet"

# Get address for mining rewards
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass getnewaddress
```

### 2.4 Issue Test Assets

```bash
# Issue tokenized BTC (1000 units)
BTC_ASSET=$(elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass issueasset 1000 0 | jq -r '.asset')
echo "BTC Asset ID: $BTC_ASSET"

# Issue USDT (100,000 units)
USDT_ASSET=$(elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass issueasset 100000 0 | jq -r '.asset')
echo "USDT Asset ID: $USDT_ASSET"

# Generate block to confirm issuances
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass generate 1

# Save asset IDs for later
echo "BTC_ASSET_ID=$BTC_ASSET" > .env.local
echo "USDT_ASSET_ID=$USDT_ASSET" >> .env.local
```

---

## Step 3: Setup Python Backend

### 3.1 Create Virtual Environment

```bash
cd backend

# Create venv
python3.11 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate
```

### 3.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-elementstx==0.1.5
httpx==0.25.1
pytest==7.4.3
pytest-asyncio==0.21.1
hypothesis==6.92.1
python-dotenv==1.0.0
```

### 3.3 Configure Environment

Create `backend/.env`:
```bash
# Elements RPC
ELEMENTS_RPC_URL=http://127.0.0.1:18884
ELEMENTS_RPC_USER=liquiduser
ELEMENTS_RPC_PASSWORD=liquidpass

# Database
DATABASE_URL=sqlite:///./fantasma.db

# Asset IDs (from Step 2.4)
BTC_ASSET_ID=<paste from .env.local>
USDT_ASSET_ID=<paste from .env.local>

# Oracle (mock for development)
ORACLE_URL=http://localhost:8001
ORACLE_PUBKEY=<mock pubkey>

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 3.4 Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_testnet.py
```

### 3.5 Start Backend

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify**: Open http://localhost:8000/docs (FastAPI Swagger UI)

---

## Step 4: Setup Frontend

### 4.1 Install Dependencies

```bash
cd frontend
npm install
```

**package.json** (key dependencies):
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.2",
    "tailwindcss": "^3.3.5",
    "@radix-ui/react-*": "latest",
    "lucide-react": "^0.292.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.8.4"
  }
}
```

### 4.2 Configure Environment

Create `frontend/.env.local`:
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_NETWORK=regtest
```

### 4.3 Start Frontend

```bash
npm start
```

**Verify**: Open http://localhost:3000

---

## Step 5: Setup SimplicityHL Validators

### 5.1 Install SimplicityHL Compiler

```bash
# Clone Simplicity repository
git clone https://github.com/BlockstreamResearch/simplicity.git
cd simplicity

# Build compiler (requires Haskell Stack)
stack build

# Add to PATH
export PATH=$PATH:$(stack path --local-bin)
```

### 5.2 Compile Validators

```bash
cd validators/reserve

# Compile Reserve validator
simplicity-hl compile reserve.simpl -o reserve.simp

# Verify compilation
simplicity-hl verify reserve.simp
```

### 5.3 Deploy to Regtest (Mock)

```bash
# For development, validators are mocked in Python
# Real deployment happens after formal verification

cd backend
python scripts/deploy_validators.py --network regtest
```

---

## Step 6: Run Tests

### 6.1 Backend Tests

```bash
cd backend

# Unit tests
pytest tests/unit/ -v

# Property-based tests
pytest tests/property/ -v --hypothesis-show-statistics

# Integration tests (requires running Elements node)
pytest tests/integration/ -v
```

### 6.2 Frontend Tests

```bash
cd frontend

# Component tests
npm test

# Coverage
npm test -- --coverage
```

---

## Step 7: Verify Setup

### 7.1 Check All Services

```bash
# Elements node
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass getblockchaininfo

# Backend API
curl http://localhost:8000/api/v1/reserves

# Frontend
curl http://localhost:3000
```

### 7.2 Test End-to-End Flow

**Supply Assets**:
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/supply \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "lq1q...",
    "asset_id": "'$BTC_ASSET_ID'",
    "amount": "100000000",
    "signature": "..."
  }'
```

**Check Position**:
```bash
curl http://localhost:8000/api/v1/positions/lq1q...
```

---

## Development Workflow

### Daily Development

1. **Start Services**:
```bash
# Terminal 1: Elements node
elementsd -regtest

# Terminal 2: Backend
cd backend && source venv/bin/activate
uvicorn src.main:app --reload

# Terminal 3: Frontend
cd frontend && npm start
```

2. **Make Changes**: Edit code in `backend/src/` or `frontend/src/`

3. **Test Changes**:
```bash
# Backend
pytest tests/

# Frontend
npm test
```

4. **Commit**:
```bash
git add .
git commit -m "feat: implement borrow operation"
git push origin 001-utxo-lending-protocol
```

### Debugging

**Backend Logs**:
```bash
# Uvicorn logs show in terminal
# Or check logs/app.log
tail -f logs/app.log
```

**Frontend Logs**:
- Open browser DevTools (F12)
- Check Console tab

**Elements Node**:
```bash
# Check debug.log
tail -f ~/.elements/regtest/debug.log
```

---

## Common Issues

### Issue: Elements RPC Connection Failed

**Solution**:
```bash
# Check node is running
ps aux | grep elementsd

# Restart node
elements-cli -regtest stop
elementsd -regtest

# Verify RPC
elements-cli -regtest -rpcuser=liquiduser -rpcpassword=liquidpass getblockchaininfo
```

### Issue: Database Migration Failed

**Solution**:
```bash
cd backend

# Reset database
rm fantasma.db

# Re-run migrations
alembic upgrade head
```

### Issue: Frontend Can't Connect to Backend

**Solution**:
- Check backend is running on port 8000
- Verify CORS settings in `backend/src/main.py`
- Check `.env.local` has correct API_URL

### Issue: RAY Math Overflow

**Solution**:
- Python's `int` is arbitrary precision (no overflow)
- Ensure all RAY operations use integer division `//`
- Check test cases in `tests/unit/test_ray_math.py`

---

## Next Steps

### Implement User Stories

1. **Supply Assets (P1)**:
   - Backend: `backend/src/api/routes/supply.py`
   - Frontend: `frontend/src/pages/Supply.tsx`
   - Tests: `backend/tests/integration/test_supply.py`

2. **Borrow Against Collateral (P2)**:
   - Backend: `backend/src/api/routes/borrow.py`
   - Frontend: `frontend/src/pages/Borrow.tsx`
   - Tests: `backend/tests/integration/test_borrow.py`

3. **Liquidate Positions (P3)**:
   - Backend: `backend/src/api/routes/liquidate.py`
   - Frontend: `frontend/src/pages/Liquidate.tsx`
   - Tests: `backend/tests/integration/test_liquidate.py`

### Formal Verification

1. Write formal specs in `validators/reserve/reserve.spec`
2. Develop Coq proofs in `validators/reserve/proofs/`
3. Verify proofs: `coqc collateralization.v`

### Deploy to Testnet

1. Get Liquid testnet coins from faucet
2. Deploy validators to testnet
3. Update `.env` with testnet RPC URL
4. Test with real testnet transactions

---

## Resources

- **Specification**: `specs/001-utxo-lending-protocol/spec.md`
- **Data Model**: `specs/001-utxo-lending-protocol/data-model.md`
- **API Docs**: http://localhost:8000/docs
- **Elements Docs**: https://elementsproject.org/
- **SimplicityHL**: https://github.com/BlockstreamResearch/simplicity
- **AAVE Docs**: https://docs.aave.com/

---

## Support

- **Issues**: https://github.com/fantasma-protocol/utxo-lending/issues
- **Discussions**: https://github.com/fantasma-protocol/utxo-lending/discussions
- **Constitution**: `.specify/memory/constitution.md`

---

**Setup Complete!** 🎉

You now have a fully functional development environment for the UTXO-based lending protocol. Start implementing user stories following the constitution principles and test-first approach.
