# Debt UTXO Binary Layout Specification

**Version**: 1.0  
**Size**: 128 bytes  
**Purpose**: On-chain state for individual debt positions

## Overview

Each Debt UTXO represents a user's borrow position with collateral. The UTXO is consumed and recreated on borrow/repay/liquidation operations.

## Binary Layout (128 bytes)

```
Offset | Size  | Field                    | Type    | Description
-------|-------|--------------------------|---------|-------------
0      | 20    | user_address             | bytes20 | Borrower's address (first 20 bytes)
20     | 32    | position_id              | uint256 | Unique position identifier
52     | 32    | borrowed_asset_id        | bytes32 | Asset being borrowed
84     | 8     | principal                | uint64  | Initial borrow amount (satoshis)
92     | 32    | borrow_index_at_open     | uint256 | Index when position opened (RAY)
124    | 4     | reserved                 | bytes4  | Future use
-------|-------|--------------------------|---------|-------------
Total: 128 bytes
```

## Collateral UTXO (Separate, 64 bytes)

Collateral is held in a separate UTXO locked to the debt position:

```
Offset | Size  | Field                    | Type    | Description
-------|-------|--------------------------|---------|-------------
0      | 32    | position_id              | uint256 | Links to debt position
32     | 32    | collateral_asset_id      | bytes32 | Asset used as collateral
64     | 8     | collateral_amount        | uint64  | Amount locked (satoshis)
72     | 8     | reserved                 | bytes8  | Future use
-------|-------|--------------------------|---------|-------------
Total: 80 bytes
```

## Field Descriptions

### user_address (20 bytes)
- First 20 bytes of user's Liquid address
- Used to identify position owner
- Cannot be changed after creation

### position_id (32 bytes)
- Unique identifier for this debt position
- Generated from transaction hash
- Used to link debt and collateral UTXOs

### borrowed_asset_id (32 bytes)
- Asset being borrowed (e.g., USDT)
- Hex-encoded, padded to 32 bytes

### principal (8 bytes)
- Initial borrowed amount in satoshis
- Never changes (interest tracked via index)
- Max: 2^64-1 satoshis

### borrow_index_at_open (32 bytes, RAY)
- Borrow index when position was created
- Used to calculate current debt
- Formula: `current_debt = principal * (current_index / borrow_index_at_open)`

### collateral_asset_id (32 bytes)
- Asset used as collateral (e.g., BTC)
- Hex-encoded, padded to 32 bytes

### collateral_amount (8 bytes)
- Amount of collateral locked
- Used for LTV and health factor calculations

## Health Factor Calculation

```
collateral_value = oracle_price(collateral_asset) * collateral_amount
debt_value = oracle_price(borrowed_asset) * current_debt
health_factor = (collateral_value * liquidation_threshold) / debt_value

where:
  current_debt = principal * (current_borrow_index / borrow_index_at_open)
```

## State Transition Rules

### Borrow Operation
```
# Create new debt position
new_position = {
  user_address: borrower,
  position_id: hash(tx_id, vout),
  borrowed_asset_id: asset,
  principal: amount,
  borrow_index_at_open: current_borrow_index,
}

# Lock collateral in separate UTXO
new_collateral = {
  position_id: position_id,
  collateral_asset_id: collateral_asset,
  collateral_amount: collateral_amount,
}

# Validate LTV
require(debt_value <= collateral_value * LTV)
```

### Repay Operation (Partial)
```
repay_amount = min(amount, current_debt)
new_principal = current_debt - repay_amount
new_borrow_index_at_open = current_borrow_index

# Proportionally release collateral
collateral_released = (collateral_amount * repay_amount) / current_debt
new_collateral_amount = collateral_amount - collateral_released
```

### Repay Operation (Full)
```
require(amount >= current_debt)
# Burn debt UTXO
# Release all collateral to user
```

### Liquidation Operation
```
require(health_factor < RAY)  # Position is unhealthy

# Liquidator repays debt
liquidation_amount = min(liquidation_max, current_debt)

# Calculate collateral to seize (with bonus)
collateral_base = (collateral_amount * liquidation_amount) / current_debt
collateral_bonus = collateral_base * LIQUIDATION_BONUS
collateral_seized = min(collateral_amount, collateral_base + collateral_bonus)

# If full liquidation, burn debt UTXO
# If partial, update position and remaining collateral
```

## Invariants to Enforce

1. **LTV Constraint**: `debt_value ≤ collateral_value * LTV`
2. **Health Factor**: `HF = (collateral_value * threshold) / debt_value`
3. **Liquidation Rule**: `HF < 1.0 → position is liquidatable`
4. **Collateral Link**: Each debt UTXO has exactly one collateral UTXO
5. **Principal Immutable**: `principal` never changes (only index updates)

## Encoding Example

```python
def encode_debt_utxo(position: DebtPosition) -> bytes:
    data = bytearray(128)
    
    # user_address (20 bytes)
    addr_bytes = decode_liquid_address(position.user_address)
    data[0:20] = addr_bytes[:20]
    
    # position_id (32 bytes)
    data[20:52] = position.id.to_bytes(32, 'big')
    
    # borrowed_asset_id (32 bytes)
    data[52:84] = bytes.fromhex(position.borrowed_asset_id).ljust(32, b'\x00')
    
    # principal (8 bytes)
    data[84:92] = position.principal.to_bytes(8, 'big')
    
    # borrow_index_at_open (32 bytes)
    data[92:124] = position.borrow_index_at_open.to_bytes(32, 'big')
    
    # reserved (4 bytes)
    data[124:128] = bytes(4)
    
    return bytes(data)

def encode_collateral_utxo(position: DebtPosition) -> bytes:
    data = bytearray(80)
    
    # position_id (32 bytes)
    data[0:32] = position.id.to_bytes(32, 'big')
    
    # collateral_asset_id (32 bytes)
    data[32:64] = bytes.fromhex(position.collateral_asset_id).ljust(32, b'\x00')
    
    # collateral_amount (8 bytes)
    data[64:72] = position.collateral_amount.to_bytes(8, 'big')
    
    # reserved (8 bytes)
    data[72:80] = bytes(8)
    
    return bytes(data)
```

## Validation Logic (SimplicityHL Pseudocode)

```
validate_borrow(collateral_value, debt_value, ltv):
  # Check LTV ratio
  max_debt = ray_mul(collateral_value, ltv)
  assert debt_value <= max_debt
  
  return True

validate_health_factor(collateral_value, debt_value, threshold):
  # Calculate health factor
  weighted_collateral = ray_mul(collateral_value, threshold)
  health_factor = ray_div(weighted_collateral, debt_value)
  
  return health_factor

validate_liquidation(position, oracle, reserve):
  # Get current debt
  current_debt = calculate_current_debt(
    position.principal,
    position.borrow_index_at_open,
    reserve.variable_borrow_index
  )
  
  # Get values from oracle
  debt_value = oracle.get_value(current_debt, position.borrowed_asset_id)
  collateral_value = oracle.get_value(position.collateral_amount, position.collateral_asset_id)
  
  # Check health factor
  health_factor = validate_health_factor(collateral_value, debt_value, LIQUIDATION_THRESHOLD)
  
  assert health_factor < RAY  # Position must be unhealthy
  
  return True

calculate_current_debt(principal, initial_index, current_index):
  # Debt accrues based on index ratio
  return ray_mul(principal * RAY, ray_div(current_index, initial_index)) / RAY
```

## Example Lifecycle

```
1. User creates position:
   - Locks 2.0 BTC as collateral ($120,000)
   - Borrows $50,000 USDT
   - LTV = 41.67% (< 75% max)
   - Health Factor = 1.92 (healthy)

2. BTC price drops to $50,000:
   - Collateral value = $100,000
   - Health Factor = 1.60 (still healthy)

3. BTC price drops to $40,000:
   - Collateral value = $80,000
   - Health Factor = 1.28 (warning)

4. BTC price drops to $32,000:
   - Collateral value = $64,000
   - Health Factor = 1.024 (close to liquidation)

5. BTC price drops to $31,000:
   - Collateral value = $62,000
   - Health Factor = 0.992 (< 1.0, liquidatable!)
   - Liquidator repays $50,000 USDT
   - Liquidator receives ~2.05 BTC ($63,550 with 5% bonus)
```

## References

- LTV: 75% (Maximum Loan-to-Value)
- Liquidation Threshold: 80%
- Liquidation Bonus: 5%
- RAY precision: 10^27
