# Fantasma Protocol Validators

**Status**: Specification Only - Awaiting SimplicityHL Toolchain

This directory contains formal specifications for on-chain validators that will enforce protocol invariants using SimplicityHL and Coq proofs.

## Overview

The Fantasma Protocol uses **UTXO-based state** on Liquid Network. Each state transition (supply, borrow, withdraw, liquidate) must be validated by on-chain validators written in SimplicityHL.

## Directory Structure

```
validators/
├── README.md (this file)
├── reserve/
│   ├── reserve.spec          # Binary layout specification (320 bytes)
│   ├── reserve.simpl         # Reserve validator logic
│   └── proofs/
│       ├── solvency.v        # Coq: totalDebt ≤ totalLiquidity
│       └── index_accrual.v   # Coq: indices monotonically increase
├── debt/
│   ├── debt.spec             # Binary layout specification (128 bytes)
│   ├── debt.simpl            # Debt validator logic
│   └── proofs/
│       └── health_factor.v   # Coq: collateralization preserved
├── oracle/
│   └── oracle_validator.simpl # Oracle signature verification
└── lib/
    └── ray_math.simpl        # RAY precision math library
```

## Implementation Status

- ✅ **Specifications Written** (T070-T072)
- ⏳ **SimplicityHL Implementation** (T073-T075) - Awaiting toolchain
- ⏳ **Coq Proofs** (T076-T078) - Awaiting implementation
- ⏳ **Compilation** (T079) - Requires `simplicity-hl` compiler
- ⏳ **Verification** (T080) - Requires Coq proofs

## Prerequisites

### SimplicityHL Toolchain
- **simplicity-hl** compiler (not yet publicly released)
- Elements Core with Simplicity support
- Simplicity runtime for Liquid Network

### Coq Proof Assistant
```bash
# Install Coq (version 8.17+)
opam install coq
```

## Core Invariants to Prove

### 1. Solvency Invariant
```
∀ reserve : Reserve,
  reserve.total_borrowed ≤ reserve.total_liquidity
```

### 2. Index Monotonicity
```
∀ reserve : Reserve, ∀ t1 t2 : Time,
  t1 < t2 →
  reserve.liquidity_index(t1) ≤ reserve.liquidity_index(t2) ∧
  reserve.variable_borrow_index(t1) ≤ reserve.variable_borrow_index(t2)
```

### 3. Health Factor Preservation
```
∀ position : DebtPosition,
  liquidatable(position) ↔ 
  (collateral_value(position) * liquidation_threshold) / debt_value(position) < RAY
```

## Validator Responsibilities

### Reserve Validator
- Validate state transitions for supply/withdraw
- Check liquidity constraints
- Verify index calculations
- Enforce reserve factor

### Debt Validator
- Validate borrow/repay operations
- Check LTV ratios (≤75%)
- Verify health factor calculations
- Enforce liquidation rules

### Oracle Validator
- Verify price feed signatures
- Check timestamp staleness (≤5 minutes)
- Validate price data format

## RAY Math Operations

All calculations use RAY precision (10^27):

```
ray_mul(a, b) = (a * b + RAY/2) / RAY
ray_div(a, b) = (a * RAY + b/2) / b
accrue_index(index, rate, dt) = index * (1 + rate * dt)
```

## Testing Strategy

1. **Unit Tests**: Test individual validator functions
2. **Property-Based Tests**: Use QuickCheck-style testing
3. **Integration Tests**: Full transaction validation
4. **Proof Verification**: `coqc` on all `.v` files

## Deployment Process (Future)

```bash
# 1. Compile validators
simplicity-hl compile reserve/reserve.simpl -o reserve.simp
simplicity-hl compile debt/debt.simpl -o debt.simp
simplicity-hl compile oracle/oracle_validator.simpl -o oracle.simp

# 2. Verify proofs
cd reserve/proofs && coqc solvency.v
cd debt/proofs && coqc health_factor.v

# 3. Deploy to Liquid testnet
elements-cli deployvalidator reserve.simp
elements-cli deployvalidator debt.simp

# 4. Test on regtest
./scripts/test_validators_regtest.sh
```

## References

- [SimplicityHL Language Spec](https://github.com/BlockstreamResearch/simplicity)
- [Elements Simplicity Integration](https://elementsproject.org/features/simplicity)
- [Coq Proof Assistant](https://coq.inria.fr/)
- [AAVE v2 Specification](https://docs.aave.com/developers/v/2.0/)

## Current MVP Status

The protocol currently runs with **simulated UTXO transactions** in the coordinator service. All business logic is implemented in Python/TypeScript. These validators will replace the simulation layer when deployed to mainnet.

**Next Steps**:
1. Monitor SimplicityHL toolchain releases
2. Implement validators once compiler is available
3. Write and verify Coq proofs
4. Deploy to Liquid testnet
5. Audit and mainnet launch
