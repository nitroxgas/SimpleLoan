# Reserve UTXO Binary Layout Specification

**Version**: 1.0  
**Size**: 320 bytes  
**Purpose**: On-chain state for lending pool reserves

## Overview

Each Reserve UTXO represents the current state of a lending pool for a specific asset. The UTXO is consumed and recreated with updated state on every supply/withdraw/borrow/repay operation.

## Binary Layout (320 bytes)

```
Offset | Size  | Field                        | Type    | Description
-------|-------|------------------------------|---------|-------------
0      | 32    | asset_id                     | bytes32 | Liquid asset ID (hex)
32     | 32    | utxo_version                 | uint256 | Version for upgrades
64     | 8     | total_liquidity              | uint64  | Total supplied (satoshis)
72     | 8     | total_borrowed               | uint64  | Total borrowed (satoshis)
80     | 32    | liquidity_index              | uint256 | Cumulative supply index (RAY)
112    | 32    | variable_borrow_index        | uint256 | Cumulative borrow index (RAY)
144    | 32    | current_liquidity_rate       | uint256 | Supply rate per sec (RAY)
176    | 32    | current_variable_borrow_rate | uint256 | Borrow rate per sec (RAY)
208    | 8     | last_update_timestamp        | uint64  | Unix timestamp (seconds)
216    | 32    | reserve_factor               | uint256 | Protocol fee % (RAY)
248    | 32    | ltv                          | uint256 | Loan-to-Value % (RAY)
280    | 32    | liquidation_threshold        | uint256 | Liquidation threshold % (RAY)
312    | 8     | reserved                     | bytes8  | Future use
-------|-------|------------------------------|---------|-------------
Total: 320 bytes
```

## Field Descriptions

### asset_id (32 bytes)
- Liquid Network asset identifier
- Hex-encoded, padded to 32 bytes
- Example: `0x6f0279e9ed041c3d710a9f57d0c02928416460c4b722ae3457a11eec381c526d` (BTC)

### utxo_version (32 bytes)
- Version number for backward compatibility
- Current: `1`
- Allows soft forks and upgrades

### total_liquidity (8 bytes)
- Sum of all supplied assets (satoshis)
- Max: 2^64-1 = ~184M BTC
- Invariant: `total_liquidity >= total_borrowed`

### total_borrowed (8 bytes)
- Sum of all borrowed assets (satoshis)
- Updated on borrow/repay
- Invariant: `total_borrowed <= total_liquidity`

### liquidity_index (32 bytes, RAY)
- Cumulative index for aToken exchange rate
- Formula: `aToken_value = aToken_amount * (liquidity_index / initial_index)`
- Starts at RAY (10^27)
- Monotonically increasing

### variable_borrow_index (32 bytes, RAY)
- Cumulative index for debt accrual
- Formula: `current_debt = principal * (current_index / initial_index)`
- Starts at RAY (10^27)
- Monotonically increasing

### current_liquidity_rate (32 bytes, RAY)
- Current supply interest rate per second
- Example: 5% APY = ~1.585e18 per second
- Calculated from utilization rate

### current_variable_borrow_rate (32 bytes, RAY)
- Current borrow interest rate per second
- Example: 10% APY = ~3.170e18 per second
- Calculated from utilization rate

### last_update_timestamp (8 bytes)
- Unix timestamp of last index update
- Used to calculate interest accrual
- Updated on every transaction

### reserve_factor (32 bytes, RAY)
- Protocol fee as percentage
- Example: 10% = 0.1 * RAY
- Range: [0, RAY]

### ltv (32 bytes, RAY)
- Maximum Loan-to-Value ratio
- Example: 75% = 0.75 * RAY
- Used for borrow validation

### liquidation_threshold (32 bytes, RAY)
- Health factor threshold
- Example: 80% = 0.80 * RAY
- Used for liquidation checks

### reserved (8 bytes)
- Reserved for future protocol upgrades
- Must be zero in v1

## State Transition Rules

### Supply Operation
```
new_total_liquidity = old_total_liquidity + amount
new_liquidity_index = accrue_index(old_liquidity_index, rate, time_delta)
```

### Withdraw Operation
```
require(new_total_liquidity >= total_borrowed)
new_total_liquidity = old_total_liquidity - amount
```

### Borrow Operation
```
require(amount <= available_liquidity)
require(check_ltv(collateral, amount))
new_total_borrowed = old_total_borrowed + amount
new_total_liquidity = old_total_liquidity - amount
```

### Index Updates
```
time_delta = current_timestamp - last_update_timestamp
new_liquidity_index = old_liquidity_index * (1 + liquidity_rate * time_delta)
new_borrow_index = old_borrow_index * (1 + borrow_rate * time_delta)
```

## Invariants to Enforce

1. **Solvency**: `total_borrowed ≤ total_liquidity`
2. **Index Monotonicity**: indices never decrease
3. **Timestamp Ordering**: `new_timestamp >= old_timestamp`
4. **Rate Bounds**: `0 ≤ rates ≤ MAX_RATE`
5. **Reserve Factor**: `0 ≤ reserve_factor ≤ RAY`

## Encoding Example

```python
def encode_reserve_utxo(reserve: ReserveState) -> bytes:
    data = bytearray(320)
    
    # asset_id (32 bytes)
    data[0:32] = bytes.fromhex(reserve.asset_id).ljust(32, b'\x00')
    
    # utxo_version (32 bytes, big-endian)
    data[32:64] = (1).to_bytes(32, 'big')
    
    # total_liquidity (8 bytes, big-endian)
    data[64:72] = reserve.total_liquidity.to_bytes(8, 'big')
    
    # total_borrowed (8 bytes, big-endian)
    data[72:80] = reserve.total_borrowed.to_bytes(8, 'big')
    
    # liquidity_index (32 bytes, big-endian)
    data[80:112] = reserve.liquidity_index.to_bytes(32, 'big')
    
    # variable_borrow_index (32 bytes, big-endian)
    data[112:144] = reserve.variable_borrow_index.to_bytes(32, 'big')
    
    # current_liquidity_rate (32 bytes, big-endian)
    data[144:176] = reserve.current_liquidity_rate.to_bytes(32, 'big')
    
    # current_variable_borrow_rate (32 bytes, big-endian)
    data[176:208] = reserve.current_variable_borrow_rate.to_bytes(32, 'big')
    
    # last_update_timestamp (8 bytes, big-endian)
    data[208:216] = reserve.last_update_timestamp.to_bytes(8, 'big')
    
    # reserve_factor (32 bytes, big-endian)
    data[216:248] = reserve.reserve_factor.to_bytes(32, 'big')
    
    # ltv (32 bytes, big-endian)
    data[248:280] = int(0.75 * 10**27).to_bytes(32, 'big')
    
    # liquidation_threshold (32 bytes, big-endian)
    data[280:312] = int(0.80 * 10**27).to_bytes(32, 'big')
    
    # reserved (8 bytes)
    data[312:320] = bytes(8)
    
    return bytes(data)
```

## Validation Logic (SimplicityHL Pseudocode)

```
validate_reserve_transition(old_reserve, new_reserve, operation):
  # Common checks
  assert new_reserve.asset_id == old_reserve.asset_id
  assert new_reserve.utxo_version == old_reserve.utxo_version
  assert new_reserve.last_update_timestamp >= old_reserve.last_update_timestamp
  
  # Solvency invariant
  assert new_reserve.total_borrowed <= new_reserve.total_liquidity
  
  # Index monotonicity
  assert new_reserve.liquidity_index >= old_reserve.liquidity_index
  assert new_reserve.variable_borrow_index >= old_reserve.variable_borrow_index
  
  # Operation-specific checks
  match operation:
    Supply(amount):
      assert new_reserve.total_liquidity == old_reserve.total_liquidity + amount
    
    Withdraw(amount):
      assert new_reserve.total_liquidity == old_reserve.total_liquidity - amount
      assert new_reserve.total_liquidity >= new_reserve.total_borrowed
    
    Borrow(amount):
      assert new_reserve.total_borrowed == old_reserve.total_borrowed + amount
      assert new_reserve.total_liquidity == old_reserve.total_liquidity - amount
```

## References

- Elements UTXO format: https://elementsproject.org/
- RAY precision: 10^27 (AAVE standard)
- Liquid asset IDs: 32-byte hex strings
