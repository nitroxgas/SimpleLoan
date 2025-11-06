# Research: UTXO-Based Lending Protocol

**Feature**: 001-utxo-lending-protocol  
**Date**: 2025-11-06  
**Phase**: 0 (Research & Technology Selection)

## Overview

This document consolidates research findings for implementing an AAVE-inspired lending protocol on Liquid Network using UTXO/SimplicityHL architecture. Research covers technology stack selection, UTXO-specific patterns, formal verification approaches, and integration strategies.

---

## 1. Python Backend & Elements SDK Integration

### Decision: Python 3.11+ with FastAPI

**Rationale**:
- **FastAPI**: Modern async framework with automatic OpenAPI documentation, Pydantic validation, and high performance
- **Python 3.11+**: Type hints, performance improvements, better async support
- **Elements SDK**: `python-elementstx` library provides Liquid Network integration

**Alternatives Considered**:
- **Rust**: Higher performance but steeper learning curve, less mature Elements bindings
- **Node.js**: Good for full-stack TypeScript but Python has better scientific computing libraries for RAY math
- **Go**: Strong concurrency but less ecosystem for DeFi/blockchain tooling

**Best Practices**:
- Use **SQLAlchemy 2.0** with async support for database operations
- Implement **Pydantic models** for request/response validation and type safety
- Use **Alembic** for database migrations
- Structure as **layered architecture**: API → Services → Models
- Implement **dependency injection** for testability (FastAPI's `Depends`)

**Key Libraries**:
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-elementstx==0.1.5  # Elements SDK
httpx==0.25.1  # Async HTTP client for oracle feeds
pytest==7.4.3
pytest-asyncio==0.21.1
hypothesis==6.92.1  # Property-based testing
```

---

## 2. Elements SDK & Liquid Network Integration

### Decision: python-elementstx + Elements Core RPC

**Rationale**:
- **python-elementstx**: Python bindings for Elements (Liquid) transactions
- **Elements Core**: Full node for Liquid testnet provides RPC interface
- **Asset Issuance**: Liquid native support for tokenized BTC/USDT

**Integration Pattern**:
```python
# backend/src/utils/liquid_client.py
from elementstx import CTransaction, CTxOut, CScript
from elementstx.core import lx, b2x
import requests

class LiquidClient:
    def __init__(self, rpc_url: str, rpc_user: str, rpc_pass: str):
        self.rpc_url = rpc_url
        self.auth = (rpc_user, rpc_pass)
    
    async def get_utxo(self, txid: str, vout: int):
        """Fetch UTXO from Elements node"""
        response = await self.rpc_call("gettxout", [txid, vout])
        return response
    
    async def broadcast_tx(self, tx_hex: str):
        """Broadcast transaction to Liquid network"""
        return await self.rpc_call("sendrawtransaction", [tx_hex])
```

**Best Practices**:
- Run **Elements Core** in regtest mode for local development
- Use **testnet** for integration testing
- Implement **UTXO caching** in SQLite to avoid repeated RPC calls
- Handle **transaction malleability** (use SegWit addresses)
- Implement **retry logic** for RPC failures

---

## 3. SimplicityHL Validators & Formal Verification

### Decision: SimplicityHL with Coq Proofs

**Rationale**:
- **SimplicityHL**: High-level language for Simplicity (Liquid's smart contract language)
- **Formal Verification**: Coq theorem prover for mathematical proofs
- **Safety**: Prevents entire classes of vulnerabilities (reentrancy, overflow, unauthorized access)

**Verification Strategy**:
1. **Formal Specification**: Write `.spec` files defining invariants
2. **Implementation**: Write `.simpl` validators matching specs
3. **Proof Development**: Prove in Coq that implementation satisfies specification
4. **Extraction**: Compile SimplicityHL to Simplicity bytecode

**Key Invariants to Prove**:
```coq
(* validators/reserve/proofs/solvency.v *)
Theorem reserve_solvency:
  forall (old_state new_state: ReserveState),
    valid_transition old_state new_state ->
    new_state.totalBorrowed <= new_state.totalLiquidity.

Theorem index_monotonic:
  forall (old_index new_index: RAY) (rate: RAY) (time: nat),
    new_index = accrue_index old_index rate time ->
    new_index >= old_index.

Theorem collateralization_preserved:
  forall (debt: DebtPosition) (collateral_value debt_value: RAY),
    health_factor debt collateral_value debt_value > RAY ->
    collateral_value * liquidation_threshold >= debt_value.
```

**Best Practices**:
- Start with **simple invariants** (monotonicity, bounds)
- Use **property-based testing** (Hypothesis) to find counterexamples before proving
- **Modular proofs**: Prove helper functions separately
- **Automated tactics**: Use Coq's `auto`, `omega` for arithmetic
- **Extraction validation**: Test extracted code matches Python reference implementation

---

## 4. RAY Fixed-Point Arithmetic (10^27)

### Decision: Pure Integer Math with RAY = 10^27

**Rationale**:
- **AAVE Standard**: RAY = 10^27 provides precision for interest calculations
- **No Floating Point**: Validators must use only integer arithmetic
- **Overflow Safety**: Use 256-bit integers (Python's `int` is arbitrary precision)

**Implementation**:
```python
# backend/src/utils/ray_math.py
RAY = 10**27
SECONDS_PER_YEAR = 31_536_000

def ray_mul(a: int, b: int) -> int:
    """Multiply two RAY values: floor(a * b / RAY)"""
    return (a * b) // RAY

def ray_div(a: int, b: int) -> int:
    """Divide two RAY values: floor(a * RAY / b)"""
    if b == 0:
        raise ValueError("Division by zero")
    return (a * RAY) // b

def accrue_index(index_old: int, annual_rate: int, time_elapsed: int) -> int:
    """
    Accrue interest index over time.
    index_new = index_old * (1 + annual_rate * time_elapsed / SECONDS_PER_YEAR)
    All values in RAY.
    """
    rate_per_second = annual_rate // SECONDS_PER_YEAR
    index_factor = RAY + (rate_per_second * time_elapsed)
    return ray_mul(index_old, index_factor)

def calculate_health_factor(
    collateral_value: int,  # in RAY
    debt_value: int,  # in RAY
    liquidation_threshold: int  # in RAY (e.g., 0.8 * RAY = 80%)
) -> int:
    """Health factor = collateral * threshold / debt"""
    if debt_value == 0:
        return RAY * 10**9  # Effectively infinite
    numerator = ray_mul(collateral_value, liquidation_threshold)
    return ray_div(numerator, debt_value)
```

**Testing Strategy**:
```python
# tests/unit/test_ray_math.py
from hypothesis import given, strategies as st
import pytest

@given(
    a=st.integers(min_value=0, max_value=10**36),
    b=st.integers(min_value=1, max_value=10**36)
)
def test_ray_mul_div_inverse(a, b):
    """Property: ray_div(ray_mul(a, b), b) ≈ a"""
    result = ray_mul(a, b)
    recovered = ray_div(result, b)
    assert abs(recovered - a) <= 1  # Allow 1 unit rounding error

def test_accrue_index_monotonic():
    """Index should never decrease"""
    index = RAY
    rate = int(0.05 * RAY)  # 5% annual
    for days in range(1, 366):
        time_elapsed = days * 86400
        new_index = accrue_index(index, rate, time_elapsed)
        assert new_index >= index
        index = new_index
```

---

## 5. Off-Chain Coordinator Pattern

### Decision: Coordinator Service with Optimistic Concurrency

**Rationale**:
- **UTXO Race Conditions**: Multiple users can't update same Reserve UTXO simultaneously
- **Coordinator**: Serializes operations, assembles valid transactions
- **User Experience**: Users submit intents, coordinator handles UTXO complexity

**Architecture**:
```python
# backend/src/services/coordinator.py
from asyncio import Queue, Lock
from dataclasses import dataclass

@dataclass
class UserIntent:
    user_id: str
    operation: str  # "supply", "borrow", "repay", "liquidate"
    amount: int
    asset_id: str
    signature: bytes

class UTXOCoordinator:
    def __init__(self, liquid_client: LiquidClient):
        self.liquid_client = liquid_client
        self.intent_queue = Queue()
        self.reserve_locks = {}  # asset_id -> Lock
    
    async def submit_intent(self, intent: UserIntent):
        """User submits operation intent"""
        await self.intent_queue.put(intent)
    
    async def process_intents(self):
        """Main coordinator loop"""
        while True:
            intent = await self.intent_queue.get()
            
            # Acquire lock for this asset's reserve
            lock = self.reserve_locks.setdefault(intent.asset_id, Lock())
            async with lock:
                try:
                    # Fetch current Reserve UTXO
                    reserve_utxo = await self.get_current_reserve(intent.asset_id)
                    
                    # Build transaction
                    tx = await self.build_transaction(intent, reserve_utxo)
                    
                    # Broadcast
                    await self.liquid_client.broadcast_tx(tx)
                    
                except Exception as e:
                    # Log failure, notify user
                    await self.notify_user(intent.user_id, f"Failed: {e}")
```

**Best Practices**:
- **Queue-based**: Serialize operations per asset
- **Locks**: Prevent concurrent Reserve UTXO updates
- **Retry Logic**: Handle temporary RPC failures
- **User Notifications**: WebSocket/SSE for real-time updates
- **Monitoring**: Track queue depth, processing latency

---

## 6. Frontend: React + TypeScript + TailwindCSS

### Decision: React 18 with TypeScript, shadcn/ui, TailwindCSS

**Rationale**:
- **React 18**: Modern hooks, concurrent rendering, large ecosystem
- **TypeScript**: Type safety, better IDE support
- **shadcn/ui**: Beautiful, accessible components built on Radix UI
- **TailwindCSS**: Utility-first CSS, rapid UI development
- **Lucide Icons**: Modern icon library

**Project Setup**:
```bash
# Create React app with TypeScript
npx create-react-app frontend --template typescript
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input form

# Install additional dependencies
npm install lucide-react axios react-query
```

**Component Structure**:
```typescript
// frontend/src/components/SupplyForm.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Coins } from 'lucide-react';

interface SupplyFormProps {
  onSubmit: (amount: number, asset: string) => Promise<void>;
}

export function SupplyForm({ onSubmit }: SupplyFormProps) {
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(parseFloat(amount), 'BTC');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center gap-2">
          <Coins className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Supply Assets</h3>
        </div>
        <Input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          step="0.00000001"
        />
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? 'Processing...' : 'Supply'}
        </Button>
      </form>
    </Card>
  );
}
```

**Best Practices**:
- **React Query**: Cache API responses, handle loading/error states
- **Custom Hooks**: `usePositions`, `useOracle` for data fetching
- **TypeScript Strict Mode**: Enable all strict checks
- **Component Testing**: Jest + React Testing Library
- **Accessibility**: Use semantic HTML, ARIA labels

---

## 7. SQLite for Off-Chain State

### Decision: SQLite with SQLAlchemy ORM

**Rationale**:
- **Local Database**: No separate database server needed
- **Fast**: In-process, low latency
- **ACID**: Transactions for consistency
- **Sufficient Scale**: MVP targets 10-50 users

**Schema Design**:
```python
# backend/src/models/position.py
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # Liquid address
    created_at = Column(DateTime, default=datetime.utcnow)
    
    supply_positions = relationship("SupplyPosition", back_populates="user")
    debt_positions = relationship("DebtPosition", back_populates="user")

class SupplyPosition(Base):
    __tablename__ = 'supply_positions'
    
    id = Column(String, primary_key=True)  # UTXO txid:vout
    user_id = Column(String, ForeignKey('users.id'))
    asset_id = Column(String)
    atoken_amount = Column(BigInteger)  # RAY precision
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="supply_positions")

class DebtPosition(Base):
    __tablename__ = 'debt_positions'
    
    id = Column(String, primary_key=True)  # UTXO txid:vout
    user_id = Column(String, ForeignKey('users.id'))
    asset_id = Column(String)
    principal = Column(BigInteger)  # Normalized principal (RAY)
    borrow_index_at_open = Column(BigInteger)  # RAY
    created_at = Column(DateTime)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="debt_positions")

class ReserveState(Base):
    __tablename__ = 'reserve_states'
    
    asset_id = Column(String, primary_key=True)
    utxo_id = Column(String)  # Current Reserve UTXO txid:vout
    total_liquidity = Column(BigInteger)
    total_variable_debt = Column(BigInteger)
    liquidity_index = Column(BigInteger)  # RAY
    variable_borrow_index = Column(BigInteger)  # RAY
    current_liquidity_rate = Column(BigInteger)  # RAY
    current_variable_borrow_rate = Column(BigInteger)  # RAY
    reserve_factor = Column(BigInteger)  # RAY
    last_update_timestamp = Column(Integer)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

**Migration Strategy**:
```bash
# Initialize Alembic
cd backend
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## 8. Oracle Integration

### Decision: Signed Price Feeds with Signature Validation

**Rationale**:
- **External Oracle**: Chainlink-style signed price feeds
- **Signature Validation**: Verify oracle pubkey signed (price, timestamp)
- **Staleness Check**: Reject prices older than 10 minutes

**Oracle Feed Structure**:
```python
# shared/types/oracle.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class OraclePriceFeed:
    asset_pair: str  # "BTC/USD"
    price: int  # Price in RAY (e.g., $50,000 = 50000 * RAY)
    timestamp: int  # Unix epoch seconds
    publisher_pubkey: bytes  # 33-byte compressed pubkey
    signature: bytes  # 64-byte Schnorr signature
    
    def verify_signature(self) -> bool:
        """Verify oracle signature"""
        message = self.asset_pair.encode() + self.price.to_bytes(32, 'big') + self.timestamp.to_bytes(8, 'big')
        # Use Liquid's Schnorr verification
        return verify_schnorr(self.publisher_pubkey, message, self.signature)
    
    def is_fresh(self, max_age_seconds: int = 600) -> bool:
        """Check if price is recent (default 10 minutes)"""
        import time
        return (time.time() - self.timestamp) < max_age_seconds
```

**Backend Integration**:
```python
# backend/src/services/oracle_service.py
import httpx

class OracleService:
    def __init__(self, oracle_url: str, trusted_pubkeys: list[bytes]):
        self.oracle_url = oracle_url
        self.trusted_pubkeys = trusted_pubkeys
    
    async def get_price(self, asset_pair: str) -> OraclePriceFeed:
        """Fetch and validate price feed"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.oracle_url}/price/{asset_pair}")
            feed = OraclePriceFeed(**response.json())
            
            # Validate
            if feed.publisher_pubkey not in self.trusted_pubkeys:
                raise ValueError("Untrusted oracle")
            if not feed.verify_signature():
                raise ValueError("Invalid signature")
            if not feed.is_fresh():
                raise ValueError("Stale price")
            
            return feed
```

---

## 9. Testing Strategy

### Decision: Multi-Layer Testing with Formal Verification

**Test Pyramid**:
1. **Unit Tests** (pytest): Test individual functions (RAY math, services)
2. **Property-Based Tests** (Hypothesis): Test invariants with random inputs
3. **Integration Tests**: Test against Liquid regtest
4. **Formal Verification**: Prove correctness of validators

**Example Property Test**:
```python
# tests/property/test_interest_accrual.py
from hypothesis import given, strategies as st, assume
from backend.src.utils.ray_math import accrue_index, RAY

@given(
    index=st.integers(min_value=RAY, max_value=10*RAY),
    rate=st.integers(min_value=0, max_value=int(0.5*RAY)),  # 0-50% annual
    time=st.integers(min_value=0, max_value=365*86400)  # 0-1 year
)
def test_index_accrual_properties(index, rate, time):
    """Test mathematical properties of index accrual"""
    new_index = accrue_index(index, rate, time)
    
    # Property 1: Index never decreases
    assert new_index >= index
    
    # Property 2: Zero rate means no change
    if rate == 0:
        assert new_index == index
    
    # Property 3: Zero time means no change
    if time == 0:
        assert new_index == index
    
    # Property 4: Bounded growth (no overflow)
    max_growth = index + ray_mul(index, rate)
    assert new_index <= max_growth
```

**Integration Test Setup**:
```bash
# scripts/run_regtest.sh
#!/bin/bash
# Start Elements Core in regtest mode
elementsd -regtest -daemon \
  -rpcuser=user \
  -rpcpassword=pass \
  -rpcport=18884 \
  -fallbackfee=0.00001

# Wait for node to start
sleep 5

# Generate initial blocks
elements-cli -regtest -rpcuser=user -rpcpassword=pass generate 101

# Issue test assets
elements-cli -regtest -rpcuser=user -rpcpassword=pass issueasset 1000 0  # BTC
elements-cli -regtest -rpcuser=user -rpcpassword=pass issueasset 100000 0  # USDT
```

---

## 10. Development Workflow

### Decision: Git Flow with Feature Branches

**Workflow**:
1. **Feature Branch**: `001-utxo-lending-protocol` (current)
2. **Development**: Implement in feature branch
3. **Testing**: All tests pass (unit, property, integration, formal)
4. **Review**: Code review + constitution compliance check
5. **Merge**: To `main` after approval

**CI/CD** (Future):
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=src
      - name: Run property tests
        run: |
          cd backend
          pytest tests/property/ -v --hypothesis-show-statistics
```

---

## Summary of Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend Language | Python 3.11+ | FastAPI, Elements SDK, scientific computing |
| Backend Framework | FastAPI | Async, OpenAPI, Pydantic validation |
| Blockchain Integration | Elements SDK | Liquid Network native support |
| Smart Contracts | SimplicityHL | Formal verification, Liquid compatibility |
| Formal Verification | Coq | Mathematical proofs of correctness |
| Fixed-Point Math | RAY (10^27) | AAVE standard, integer-only arithmetic |
| Coordinator Pattern | Queue + Locks | Handle UTXO race conditions |
| Frontend Framework | React 18 + TypeScript | Modern, type-safe, large ecosystem |
| UI Library | shadcn/ui + TailwindCSS | Beautiful, accessible, rapid development |
| Database | SQLite | Local, fast, sufficient for MVP scale |
| ORM | SQLAlchemy 2.0 | Async support, type hints, migrations |
| Testing | pytest + Hypothesis + Jest | Unit, property-based, component tests |
| Oracle | Signed Price Feeds | Chainlink-style, signature validation |

---

## Next Steps (Phase 1)

1. **Data Model**: Define SQLAlchemy models, UTXO structures
2. **API Contracts**: OpenAPI spec for backend endpoints
3. **Quickstart**: Developer setup guide
4. **Validator Specs**: Formal specifications for Reserve/Debt validators

All research findings are now consolidated. Proceeding to Phase 1 design.
