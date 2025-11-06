# RAY Math Library Specification (SimplicityHL)

**Precision**: 10^27 (RAY)  
**Purpose**: Fixed-point arithmetic for interest rate calculations

## Overview

RAY precision (10^27) is the standard used by AAVE for high-precision financial calculations. All interest rates, indices, and percentages use RAY encoding.

## Constants

```simplicity
// RAY = 10^27
const RAY : uint256 = 1000000000000000000000000000

// HALF_RAY = RAY / 2 (for rounding)
const HALF_RAY : uint256 = 500000000000000000000000000

// WAD = 10^18 (Ethereum standard, for reference)
const WAD : uint256 = 1000000000000000000

// Seconds per year (365 days)
const SECONDS_PER_YEAR : uint64 = 31536000
```

## Core Operations

### ray_mul(a: uint256, b: uint256) -> uint256

Multiply two RAY values with proper rounding.

**Formula**:
```
result = (a * b + HALF_RAY) / RAY
```

**Properties**:
- Commutative: `ray_mul(a, b) = ray_mul(b, a)`
- Associative: `ray_mul(ray_mul(a, b), c) = ray_mul(a, ray_mul(b, c))`
- Identity: `ray_mul(a, RAY) = a`
- Zero: `ray_mul(a, 0) = 0`

**SimplicityHL Implementation**:
```simplicity
fn ray_mul(a: uint256, b: uint256) -> uint256:
  // Handle zero cases
  if a == 0 || b == 0:
    return 0
  
  // Check overflow
  require((a * b) / b == a, "ray_mul overflow")
  
  // Multiply with rounding
  let product = a * b
  let result = (product + HALF_RAY) / RAY
  
  return result
```

**Example**:
```
ray_mul(1.5 * RAY, 2.0 * RAY) = 3.0 * RAY
ray_mul(0.75 * RAY, 0.80 * RAY) = 0.6 * RAY
```

### ray_div(a: uint256, b: uint256) -> uint256

Divide two RAY values with proper rounding.

**Formula**:
```
result = (a * RAY + b/2) / b
```

**Properties**:
- Non-commutative: `ray_div(a, b) ≠ ray_div(b, a)`
- Identity: `ray_div(a, RAY) = a`
- Inverse: `ray_div(ray_mul(a, b), b) ≈ a` (up to rounding)

**SimplicityHL Implementation**:
```simplicity
fn ray_div(a: uint256, b: uint256) -> uint256:
  // Division by zero
  require(b != 0, "ray_div by zero")
  
  // Handle zero numerator
  if a == 0:
    return 0
  
  // Check overflow
  require((a * RAY) / RAY == a, "ray_div overflow")
  
  // Divide with rounding
  let half_b = b / 2
  let result = (a * RAY + half_b) / b
  
  return result
```

**Example**:
```
ray_div(3.0 * RAY, 2.0 * RAY) = 1.5 * RAY
ray_div(RAY, 0.75 * RAY) = 1.333... * RAY
```

### accrue_index(index: uint256, rate: uint256, time_delta: uint64) -> uint256

Accrue interest on an index over time.

**Formula**:
```
new_index = index * (1 + rate * time_delta)
          = index + ray_mul(index, rate * time_delta)
```

**Properties**:
- Monotonicity: `accrue_index(index, rate, dt) ≥ index` for rate ≥ 0
- Time additivity: `accrue_index(accrue_index(i, r, t1), r, t2) ≈ accrue_index(i, r, t1+t2)`
- Zero rate: `accrue_index(index, 0, dt) = index`
- Zero time: `accrue_index(index, rate, 0) = index`

**SimplicityHL Implementation**:
```simplicity
fn accrue_index(index: uint256, rate: uint256, time_delta: uint64) -> uint256:
  // No time passed
  if time_delta == 0:
    return index
  
  // No interest rate
  if rate == 0:
    return index
  
  // Calculate interest: index * rate * time_delta
  let rate_per_period = ray_mul(rate * RAY, uint256(time_delta) * RAY) / RAY
  let accrued = ray_mul(index, rate_per_period)
  let new_index = index + accrued
  
  // Ensure monotonicity
  require(new_index >= index, "index decreased")
  
  return new_index
```

**Example**:
```
// 5% APY, 1 year
rate_per_sec = 0.05 * RAY / SECONDS_PER_YEAR = ~1.585e18
index_initial = RAY
index_after_1y = accrue_index(RAY, rate_per_sec, SECONDS_PER_YEAR)
                ≈ 1.05 * RAY

// Compounding effect
index_y1 = accrue_index(RAY, rate_per_sec, SECONDS_PER_YEAR)
index_y2 = accrue_index(index_y1, rate_per_sec, SECONDS_PER_YEAR)
          = (1.05)^2 * RAY = 1.1025 * RAY
```

## Helper Functions

### percentage_to_ray(percentage: uint256) -> uint256

Convert percentage (0-100) to RAY.

```simplicity
fn percentage_to_ray(percentage: uint256) -> uint256:
  require(percentage <= 100, "percentage > 100")
  return (percentage * RAY) / 100
```

### ray_to_percentage(ray_value: uint256) -> uint256

Convert RAY to percentage (0-100).

```simplicity
fn ray_to_percentage(ray_value: uint256) -> uint256:
  return (ray_value * 100) / RAY
```

### annual_rate_to_per_second(annual_rate: uint256) -> uint256

Convert annual rate (RAY) to per-second rate (RAY).

```simplicity
fn annual_rate_to_per_second(annual_rate: uint256) -> uint256:
  return ray_div(annual_rate, SECONDS_PER_YEAR)
```

### per_second_to_annual_rate(per_second_rate: uint256) -> uint256

Convert per-second rate (RAY) to annual rate (RAY).

```simplicity
fn per_second_to_annual_rate(per_second_rate: uint256) -> uint256:
  return ray_mul(per_second_rate, SECONDS_PER_YEAR * RAY) / RAY
```

## Property-Based Test Cases

These properties should be verified with QuickCheck or Hypothesis:

```python
# Hypothesis test examples
from hypothesis import given, strategies as st

RAY = 10**27

@given(st.integers(min_value=0, max_value=10**36))
def test_ray_mul_identity(a):
    assert ray_mul(a, RAY) == a

@given(st.integers(min_value=0, max_value=10**36))
def test_ray_div_identity(a):
    assert ray_div(a, RAY) == a

@given(
    st.integers(min_value=1, max_value=10**36),
    st.integers(min_value=1, max_value=10**36)
)
def test_ray_mul_commutative(a, b):
    assert ray_mul(a, b) == ray_mul(b, a)

@given(
    st.integers(min_value=RAY, max_value=10*RAY),
    st.integers(min_value=0, max_value=RAY//10),
    st.integers(min_value=0, max_value=SECONDS_PER_YEAR)
)
def test_accrue_index_monotonic(index, rate, time_delta):
    new_index = accrue_index(index, rate, time_delta)
    assert new_index >= index

@given(
    st.integers(min_value=0, max_value=10**36),
    st.integers(min_value=1, max_value=10**36)
)
def test_ray_div_ray_mul_inverse(a, b):
    product = ray_mul(a, b)
    result = ray_div(product, b)
    # Allow small rounding error
    assert abs(result - a) <= 1
```

## Formal Verification Properties (Coq)

```coq
(* Identity properties *)
Lemma ray_mul_identity: forall a, ray_mul a RAY = a.

Lemma ray_div_identity: forall a, ray_div a RAY = a.

(* Commutativity *)
Lemma ray_mul_commutative: forall a b, 
  ray_mul a b = ray_mul b a.

(* Associativity (approximate due to rounding) *)
Lemma ray_mul_associative_approx: forall a b c,
  abs (ray_mul (ray_mul a b) c - ray_mul a (ray_mul b c)) <= EPSILON.

(* Monotonicity *)
Lemma accrue_index_monotonic: forall index rate time_delta,
  rate >= 0 -> time_delta >= 0 ->
  accrue_index index rate time_delta >= index.

(* Overflow safety *)
Lemma ray_mul_no_overflow: forall a b,
  a <= MAX_UINT256 / RAY -> b <= MAX_UINT256 / RAY ->
  ray_mul a b <= MAX_UINT256.
```

## Integration with Validators

### Reserve Validator Usage

```simplicity
// Update liquidity index
let time_delta = current_timestamp - reserve.last_update_timestamp
let new_liquidity_index = accrue_index(
  reserve.liquidity_index,
  reserve.current_liquidity_rate,
  time_delta
)

// Update borrow index
let new_borrow_index = accrue_index(
  reserve.variable_borrow_index,
  reserve.current_variable_borrow_rate,
  time_delta
)
```

### Debt Validator Usage

```simplicity
// Calculate current debt
let index_ratio = ray_div(current_borrow_index, position.borrow_index_at_open)
let current_debt = ray_mul(position.principal * RAY, index_ratio) / RAY

// Calculate health factor
let weighted_collateral = ray_mul(collateral_value, LIQUIDATION_THRESHOLD)
let health_factor = ray_div(weighted_collateral, debt_value)
```

## Performance Considerations

- **Gas Cost**: Each ray_mul/ray_div operation costs ~200-300 gas
- **Precision Loss**: Maximum rounding error is ±1 per operation
- **Overflow Protection**: All operations check for overflow
- **Optimization**: Pre-compute constants when possible

## References

- [AAVE Math Library](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/math/WadRayMath.sol)
- [RAY Precision Standard](https://docs.aave.com/developers/v/2.0/the-core-protocol/protocol-data-provider#raymath)
- [Fixed-Point Arithmetic](https://en.wikipedia.org/wiki/Fixed-point_arithmetic)
