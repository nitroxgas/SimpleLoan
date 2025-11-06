# Data Model: UTXO-Based Lending Protocol

**Feature**: 001-utxo-lending-protocol  
**Date**: 2025-11-06  
**Phase**: 1 (Design)

## Overview

This document defines the data model for the UTXO-based lending protocol, covering both on-chain (UTXO structures) and off-chain (SQLite database) entities. The model supports AAVE-inspired lending with cumulative index accounting adapted for UTXO architecture.

---

## 1. On-Chain Data Structures (UTXOs)

### 1.1 Reserve UTXO

Represents the global state of a lending pool for a specific asset.

**Binary Layout** (~320 bytes):

| Offset | Size (bytes) | Field | Type | Description |
|--------|--------------|-------|------|-------------|
| 0 | 1 | version | u8 | Layout version (0x01) |
| 1 | 32 | asset_id | bytes32 | Liquid asset ID |
| 33 | 32 | total_liquidity | uint256 | Total underlying supplied (asset units) |
| 65 | 32 | total_variable_debt | uint256 | Total borrowed (asset units) |
| 97 | 32 | liquidity_index | uint256 | aToken conversion rate (RAY) |
| 129 | 32 | variable_borrow_index | uint256 | Debt normalization index (RAY) |
| 161 | 32 | current_liquidity_rate | uint256 | Supply APY (RAY) |
| 193 | 32 | current_variable_borrow_rate | uint256 | Borrow APY (RAY) |
| 225 | 32 | reserve_factor | uint256 | Protocol fee fraction (RAY, e.g., 0.1 * RAY = 10%) |
| 257 | 8 | last_update_timestamp | uint64 | Unix epoch seconds |
| 265 | 8 | decimals | uint64 | Asset decimals (e.g., 8 for BTC) |
| 273 | 4 | flags | uint32 | Bitfield: borrowing_enabled, collateral_enabled, paused |

**Invariants**:
- `total_variable_debt <= total_liquidity` (solvency)
- `liquidity_index >= RAY` (monotonically increasing)
- `variable_borrow_index >= RAY` (monotonically increasing)
- `last_update_timestamp` increases with each update

**State Transitions**:
```
Supply:   total_liquidity += amount, liquidity_index accrues
Withdraw: total_liquidity -= amount, liquidity_index accrues
Borrow:   total_variable_debt += amount, variable_borrow_index accrues
Repay:    total_variable_debt -= amount, variable_borrow_index accrues
```

---

### 1.2 Debt UTXO

Represents a user's borrowing position for a specific asset.

**Binary Layout** (~128 bytes):

| Offset | Size (bytes) | Field | Type | Description |
|--------|--------------|-------|------|-------------|
| 0 | 1 | version | u8 | Layout version (0x01) |
| 1 | 32 | owner_pubkey_hash | bytes32 | Borrower's pubkey hash |
| 33 | 32 | principal | uint256 | Normalized principal (RAY) |
| 65 | 32 | borrow_index_at_open | uint256 | variableBorrowIndex when position opened (RAY) |
| 97 | 32 | collateral_asset_id | bytes32 | Asset used as collateral |
| 129 | 8 | last_update_timestamp | uint64 | Unix epoch seconds |
| 137 | 4 | flags | uint32 | Bitfield: rate_mode, frozen |

**Debt Calculation**:
```
current_debt = principal * variable_borrow_index / borrow_index_at_open
```

**Health Factor Calculation**:
```
collateral_value = get_oracle_price(collateral_asset_id) * collateral_amount
debt_value = get_oracle_price(borrowed_asset_id) * current_debt
health_factor = (collateral_value * liquidation_threshold) / debt_value
```

**Invariants**:
- `principal > 0` (non-zero debt)
- `borrow_index_at_open >= RAY`
- `health_factor >= 1.0 * RAY` (or liquidatable)

---

### 1.3 aToken (Supply Position)

Represents a user's supplied assets. Implemented as Liquid issued asset.

**Representation**:
- **Fungible Asset**: Each reserve has corresponding aToken asset ID
- **Amount**: User holds N aTokens
- **Value**: `underlying_value = atoken_amount * liquidity_index / RAY`

**Minting Formula**:
```
When user supplies X underlying:
  atoken_amount = X * RAY / liquidity_index
```

**Burning Formula**:
```
When user withdraws:
  underlying_received = atoken_amount * liquidity_index / RAY
```

**No UTXO Structure**: Uses Liquid's native asset issuance, tracked by asset ID + user balance.

---

### 1.4 Oracle Price Feed

External signed price data referenced by transactions.

**Structure** (not stored as UTXO, passed in transaction witness):

| Field | Type | Description |
|-------|------|-------------|
| asset_pair | string | "BTC/USD", "USDT/USD" |
| price | uint256 | Price in RAY (e.g., $50,000 = 50000 * RAY) |
| timestamp | uint64 | Unix epoch seconds |
| publisher_pubkey | bytes33 | Compressed Schnorr pubkey |
| signature | bytes64 | Schnorr signature over (asset_pair \|\| price \|\| timestamp) |

**Validation**:
- Verify signature against trusted oracle pubkey
- Check `current_time - timestamp < 600` (10-minute staleness threshold)

---

## 2. Off-Chain Data Model (SQLite)

### 2.1 Users Table

Tracks user accounts and metadata.

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- Liquid address (bech32)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    total_supplied_usd INTEGER,       -- Cached total value (RAY)
    total_borrowed_usd INTEGER,       -- Cached total value (RAY)
    health_factor INTEGER             -- Cached health factor (RAY)
);

CREATE INDEX idx_users_health ON users(health_factor);
```

**Relationships**:
- One user → Many supply positions
- One user → Many debt positions

---

### 2.2 Supply Positions Table

Mirrors on-chain aToken holdings.

```sql
CREATE TABLE supply_positions (
    id TEXT PRIMARY KEY,              -- UTXO reference or position ID
    user_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,           -- Liquid asset ID
    atoken_amount INTEGER NOT NULL,   -- RAY precision
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (asset_id) REFERENCES reserve_states(asset_id)
);

CREATE INDEX idx_supply_user ON supply_positions(user_id);
CREATE INDEX idx_supply_asset ON supply_positions(asset_id);
```

**Computed Fields** (not stored, calculated on query):
- `underlying_value = atoken_amount * reserve.liquidity_index / RAY`

---

### 2.3 Debt Positions Table

Mirrors on-chain Debt UTXOs.

```sql
CREATE TABLE debt_positions (
    id TEXT PRIMARY KEY,              -- UTXO txid:vout
    user_id TEXT NOT NULL,
    borrowed_asset_id TEXT NOT NULL,
    collateral_asset_id TEXT NOT NULL,
    principal INTEGER NOT NULL,       -- Normalized principal (RAY)
    borrow_index_at_open INTEGER NOT NULL,  -- RAY
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (borrowed_asset_id) REFERENCES reserve_states(asset_id),
    FOREIGN KEY (collateral_asset_id) REFERENCES reserve_states(asset_id)
);

CREATE INDEX idx_debt_user ON debt_positions(user_id);
CREATE INDEX idx_debt_borrowed_asset ON debt_positions(borrowed_asset_id);
```

**Computed Fields**:
- `current_debt = principal * reserve.variable_borrow_index / borrow_index_at_open`

---

### 2.4 Reserve States Table

Mirrors on-chain Reserve UTXOs.

```sql
CREATE TABLE reserve_states (
    asset_id TEXT PRIMARY KEY,        -- Liquid asset ID
    utxo_id TEXT NOT NULL,            -- Current Reserve UTXO txid:vout
    total_liquidity INTEGER NOT NULL, -- RAY
    total_variable_debt INTEGER NOT NULL,  -- RAY
    liquidity_index INTEGER NOT NULL, -- RAY
    variable_borrow_index INTEGER NOT NULL,  -- RAY
    current_liquidity_rate INTEGER NOT NULL,  -- RAY (annual)
    current_variable_borrow_rate INTEGER NOT NULL,  -- RAY (annual)
    reserve_factor INTEGER NOT NULL,  -- RAY
    last_update_timestamp INTEGER NOT NULL,  -- Unix epoch
    decimals INTEGER NOT NULL,
    flags INTEGER NOT NULL,           -- Bitfield
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Computed Fields**:
- `utilization_rate = total_variable_debt / total_liquidity` (if total_liquidity > 0)
- `available_liquidity = total_liquidity - total_variable_debt`

---

### 2.5 Transactions Table

Audit log of all operations.

```sql
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,              -- Liquid txid
    user_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,     -- "supply", "withdraw", "borrow", "repay", "liquidate"
    asset_id TEXT NOT NULL,
    amount INTEGER NOT NULL,          -- RAY
    timestamp INTEGER NOT NULL,       -- Unix epoch
    block_height INTEGER,
    status TEXT NOT NULL,             -- "pending", "confirmed", "failed"
    error_message TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (asset_id) REFERENCES reserve_states(asset_id)
);

CREATE INDEX idx_tx_user ON transactions(user_id);
CREATE INDEX idx_tx_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_tx_status ON transactions(status);
```

---

### 2.6 Oracle Prices Table

Caches oracle price feeds.

```sql
CREATE TABLE oracle_prices (
    asset_pair TEXT NOT NULL,         -- "BTC/USD"
    price INTEGER NOT NULL,           -- RAY
    timestamp INTEGER NOT NULL,       -- Unix epoch
    publisher_pubkey BLOB NOT NULL,   -- 33 bytes
    signature BLOB NOT NULL,          -- 64 bytes
    verified BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (asset_pair, timestamp)
);

CREATE INDEX idx_oracle_timestamp ON oracle_prices(asset_pair, timestamp DESC);
```

**Staleness Check**:
```sql
SELECT price FROM oracle_prices
WHERE asset_pair = 'BTC/USD'
  AND timestamp > (strftime('%s', 'now') - 600)  -- Last 10 minutes
  AND verified = TRUE
ORDER BY timestamp DESC
LIMIT 1;
```

---

## 3. Entity Relationships

### 3.1 ER Diagram

```
┌─────────┐
│  Users  │
└────┬────┘
     │
     ├──────────┬──────────────┐
     │          │              │
     ▼          ▼              ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐
│ Supply  │ │   Debt   │ │ Transactions │
│Position │ │ Position │ └──────────────┘
└────┬────┘ └────┬─────┘
     │           │
     │           │
     ▼           ▼
┌──────────────────┐
│  Reserve States  │
└────────┬─────────┘
         │
         ▼
┌──────────────┐
│Oracle Prices │
└──────────────┘
```

### 3.2 Cardinality

- **User** : **Supply Position** = 1 : N
- **User** : **Debt Position** = 1 : N
- **User** : **Transaction** = 1 : N
- **Reserve State** : **Supply Position** = 1 : N
- **Reserve State** : **Debt Position** = 1 : N (per borrowed asset)
- **Reserve State** : **Oracle Price** = 1 : N (historical prices)

---

## 4. State Transition Rules

### 4.1 Supply Operation

**Preconditions**:
- User has X underlying tokens
- Reserve exists for asset

**State Changes**:
1. **On-Chain**:
   - Consume: User's underlying UTXO (X tokens)
   - Consume: Reserve UTXO (old state)
   - Create: Reserve UTXO (new state with `total_liquidity += X`, accrued indices)
   - Create: aToken UTXO to user (`amount = X * RAY / liquidity_index`)

2. **Off-Chain**:
   - Insert/Update `supply_positions` (user_id, asset_id, atoken_amount)
   - Update `reserve_states` (total_liquidity, indices, timestamp)
   - Insert `transactions` (operation_type="supply")

**Invariants Preserved**:
- `total_liquidity` increases by X
- `liquidity_index` accrues based on time elapsed
- User receives proportional aTokens

---

### 4.2 Borrow Operation

**Preconditions**:
- User has collateral (aTokens or other assets)
- `health_factor > 1.0 * RAY` after borrow
- `amount <= available_liquidity`

**State Changes**:
1. **On-Chain**:
   - Consume: Reserve UTXO (old state)
   - Consume: Existing Debt UTXO (if any)
   - Create: Reserve UTXO (new state with `total_variable_debt += amount`, accrued indices)
   - Create: Debt UTXO (principal, borrow_index_at_open)
   - Create: Underlying token UTXO to user (amount)

2. **Off-Chain**:
   - Insert/Update `debt_positions`
   - Update `reserve_states`
   - Insert `transactions` (operation_type="borrow")
   - Update `users` (health_factor)

**Invariants Preserved**:
- `total_variable_debt` increases by amount
- `health_factor >= 1.0 * RAY`
- `total_variable_debt <= total_liquidity`

---

### 4.3 Liquidation Operation

**Preconditions**:
- Target debt position has `health_factor < 1.0 * RAY`
- Liquidator has repayment tokens

**State Changes**:
1. **On-Chain**:
   - Consume: Debt UTXO (unhealthy position)
   - Consume: Collateral aToken UTXO
   - Consume: Reserve UTXO
   - Consume: Liquidator payment UTXO
   - Create: Reserve UTXO (debt reduced)
   - Create: Collateral UTXO to liquidator (with bonus)
   - Create: Debt UTXO (if partially liquidated) or burn (if fully liquidated)

2. **Off-Chain**:
   - Update/Delete `debt_positions`
   - Update `reserve_states`
   - Insert `transactions` (operation_type="liquidate")
   - Update `users` (health_factor)

**Invariants Preserved**:
- Liquidator receives collateral at discount
- Debt reduced or eliminated
- Protocol solvency maintained

---

## 5. Data Validation Rules

### 5.1 Reserve State Validation

```python
def validate_reserve_state(reserve: ReserveState) -> bool:
    # Solvency
    assert reserve.total_variable_debt <= reserve.total_liquidity
    
    # Index bounds
    assert reserve.liquidity_index >= RAY
    assert reserve.variable_borrow_index >= RAY
    
    # Rate bounds (0-100% annual)
    assert 0 <= reserve.current_liquidity_rate <= RAY
    assert 0 <= reserve.current_variable_borrow_rate <= RAY
    
    # Reserve factor (0-100%)
    assert 0 <= reserve.reserve_factor <= RAY
    
    # Timestamp
    assert reserve.last_update_timestamp > 0
    
    return True
```

### 5.2 Debt Position Validation

```python
def validate_debt_position(debt: DebtPosition, reserve: ReserveState, oracle: OracleService) -> bool:
    # Non-zero principal
    assert debt.principal > 0
    
    # Valid index
    assert debt.borrow_index_at_open >= RAY
    
    # Health factor (if not being liquidated)
    collateral_value = get_collateral_value(debt, oracle)
    debt_value = get_debt_value(debt, reserve, oracle)
    health_factor = calculate_health_factor(collateral_value, debt_value, LIQUIDATION_THRESHOLD)
    
    # Allow health_factor < RAY only during liquidation
    return True  # Validation happens in transaction
```

---

## 6. Query Patterns

### 6.1 Get User Portfolio

```sql
SELECT 
    u.id AS user_id,
    u.health_factor,
    sp.asset_id AS supplied_asset,
    sp.atoken_amount,
    (sp.atoken_amount * rs_supply.liquidity_index / 1000000000000000000000000000) AS supplied_value,
    dp.borrowed_asset_id,
    dp.principal,
    (dp.principal * rs_borrow.variable_borrow_index / dp.borrow_index_at_open) AS borrowed_value
FROM users u
LEFT JOIN supply_positions sp ON u.id = sp.user_id
LEFT JOIN reserve_states rs_supply ON sp.asset_id = rs_supply.asset_id
LEFT JOIN debt_positions dp ON u.id = dp.user_id
LEFT JOIN reserve_states rs_borrow ON dp.borrowed_asset_id = rs_borrow.asset_id
WHERE u.id = ?;
```

### 6.2 Find Liquidatable Positions

```sql
SELECT 
    u.id,
    u.health_factor,
    dp.id AS debt_position_id,
    dp.borrowed_asset_id,
    dp.collateral_asset_id,
    (dp.principal * rs.variable_borrow_index / dp.borrow_index_at_open) AS current_debt
FROM users u
JOIN debt_positions dp ON u.id = dp.user_id
JOIN reserve_states rs ON dp.borrowed_asset_id = rs.asset_id
WHERE u.health_factor < 1000000000000000000000000000  -- < 1.0 * RAY
ORDER BY u.health_factor ASC;
```

### 6.3 Get Reserve Utilization

```sql
SELECT 
    asset_id,
    total_liquidity,
    total_variable_debt,
    (total_variable_debt * 100 / NULLIF(total_liquidity, 0)) AS utilization_percent,
    (total_liquidity - total_variable_debt) AS available_liquidity
FROM reserve_states
WHERE total_liquidity > 0;
```

---

## 7. Data Migration Strategy

### 7.1 Initial Schema

```bash
# backend/alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Create Date: 2025-11-06
"""

def upgrade():
    # Create all tables
    op.create_table('users', ...)
    op.create_table('reserve_states', ...)
    op.create_table('supply_positions', ...)
    op.create_table('debt_positions', ...)
    op.create_table('transactions', ...)
    op.create_table('oracle_prices', ...)
    
    # Create indices
    op.create_index('idx_users_health', 'users', ['health_factor'])
    # ... more indices

def downgrade():
    op.drop_table('oracle_prices')
    op.drop_table('transactions')
    op.drop_table('debt_positions')
    op.drop_table('supply_positions')
    op.drop_table('reserve_states')
    op.drop_table('users')
```

### 7.2 Seed Data (Testnet)

```python
# scripts/seed_testnet.py
from backend.src.models import ReserveState
from backend.src.utils.ray_math import RAY

def seed_reserves():
    """Initialize BTC and USDT reserves"""
    btc_reserve = ReserveState(
        asset_id="<BTC_ASSET_ID>",
        utxo_id="genesis:0",
        total_liquidity=0,
        total_variable_debt=0,
        liquidity_index=RAY,  # Start at 1.0
        variable_borrow_index=RAY,
        current_liquidity_rate=int(0.02 * RAY),  # 2% APY
        current_variable_borrow_rate=int(0.05 * RAY),  # 5% APY
        reserve_factor=int(0.1 * RAY),  # 10% protocol fee
        last_update_timestamp=int(time.time()),
        decimals=8,
        flags=0b111  # borrowing_enabled, collateral_enabled, not paused
    )
    # ... similar for USDT
```

---

## Summary

This data model provides:
- **On-chain structures**: Reserve UTXO (~320B), Debt UTXO (~128B), aToken (asset issuance)
- **Off-chain database**: SQLite with 6 tables (users, positions, reserves, transactions, oracles)
- **State transitions**: Clear rules for supply, borrow, repay, liquidate operations
- **Validation**: Invariants enforced at both on-chain (validators) and off-chain (API) layers
- **Query patterns**: Efficient lookups for user portfolios, liquidations, reserve stats

All entities align with functional requirements FR-001 through FR-036 and support the 5 core user stories.
