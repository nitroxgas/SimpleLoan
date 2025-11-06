# Feature Specification: UTXO-Based Lending Protocol

**Feature Branch**: `001-utxo-lending-protocol`  
**Created**: 2025-11-06  
**Status**: Draft  
**Input**: User description: "implementar um sistema de lending inspirado na AAVE, usando UTXO/SimplicityHL, para rodar na testnet da rede Liquid, adaptado às diferenças fundamentais do modelo UTXO/SimplicityHL"

## Clarifications

### Session 2025-11-06

- Q: Should aToken balances be updated per-user on each block or use cumulative index accounting? → A: Use cumulative index (liquidityIndex) to minimize UTXO writes - aToken amount stays constant, value increases via index
- Q: What fixed-point precision should be used for interest calculations? → A: RAY = 10^27 (AAVE standard) for all indices and rates
- Q: How to handle UTXO race conditions when multiple users access same Reserve UTXO? → A: Use off-chain coordinator (relayer pattern) + optimistic concurrency - failed transactions retry with updated state
- Q: Should confidential transactions be used for privacy? → A: No for MVP - confidential transactions complicate oracle price checks and accounting
- Q: What is the difference between LTV and liquidation threshold? → A: LTV (Loan-to-Value) determines max borrow amount; liquidation threshold is lower value triggering liquidation
- Q: Should both stable and variable rate borrowing be supported? → A: Focus on variable rate only for MVP; stable rates can be added later
- Q: How should reserve fees (protocol revenue) be handled? → A: Use reserveFactor parameter (e.g., 10%) that directs portion of interest to protocol treasury

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Supply Assets to Lending Pool (Priority: P1)

A liquidity provider wants to deposit tokenized BTC into a lending pool to earn interest on their idle assets. They create a transaction that locks their tokens in a reserve UTXO, receiving a proportional share of the pool that accrues interest over time.

**Why this priority**: This is the foundational operation - without liquidity providers supplying assets, there's nothing to lend. This creates the supply side of the lending market and must work before any borrowing can occur.

**Independent Test**: Can be fully tested by depositing tokenized BTC to a reserve pool and verifying the user receives a proportional claim that increases in value as interest accrues, then withdrawing to confirm the mechanism works end-to-end.

**Acceptance Scenarios**:

1. **Given** a user holds 1.0 tokenized BTC, **When** they supply it to the lending pool, **Then** they receive a reserve position UTXO representing their share of the pool
2. **Given** a user has a reserve position, **When** time passes and borrowers pay interest, **Then** their position value increases proportionally to their share
3. **Given** a user has a reserve position with no active borrows against it, **When** they withdraw their full balance, **Then** they receive their original deposit plus accrued interest
4. **Given** multiple users supply to the same pool, **When** interest accrues, **Then** each user's share increases proportionally to their contribution

---

### User Story 2 - Borrow Against Collateral (Priority: P2)

A borrower wants to take a loan by providing collateral. They deposit tokenized BTC as collateral and borrow USDT against it, maintaining a health factor above the liquidation threshold. The system tracks their debt position and allows repayment.

**Why this priority**: This is the core value proposition - enabling users to access liquidity without selling their assets. Requires the supply side (P1) to be functional first.

**Independent Test**: Can be tested by depositing collateral, borrowing against it up to the allowed limit, verifying the debt position is tracked correctly, and repaying the loan to reclaim collateral.

**Acceptance Scenarios**:

1. **Given** a user deposits 2.0 tokenized BTC as collateral (worth $100k at $50k/BTC), **When** they borrow $50k USDT at 150% collateralization ratio, **Then** a debt position UTXO is created tracking their loan
2. **Given** a user has an active debt position, **When** they make a partial repayment of $25k USDT, **Then** their debt decreases and available collateral to withdraw increases proportionally
3. **Given** a user has an active debt position, **When** they repay the full loan amount plus accrued interest, **Then** their collateral is fully released
4. **Given** a user has collateral deposited, **When** they attempt to borrow more than the collateralization ratio allows, **Then** the transaction is rejected
5. **Given** a user has an active loan, **When** interest accrues over time, **Then** their debt position increases according to the interest rate model

---

### User Story 3 - Liquidate Undercollateralized Positions (Priority: P3)

A liquidator monitors debt positions and liquidates those that fall below the minimum health factor. When collateral value drops or debt increases beyond safe thresholds, liquidators can purchase the collateral at a discount to restore protocol solvency.

**Why this priority**: Essential for protocol safety and solvency, but requires both supply (P1) and borrowing (P2) to be functional. Liquidations only occur when positions become unhealthy.

**Independent Test**: Can be tested by creating a debt position, simulating a price drop that makes it undercollateralized, and having a liquidator execute a liquidation transaction to claim discounted collateral.

**Acceptance Scenarios**:

1. **Given** a debt position with health factor below 1.0 (undercollateralized), **When** a liquidator submits a liquidation transaction, **Then** they receive the collateral at a discount and the debt is reduced or cleared
2. **Given** multiple undercollateralized positions exist, **When** a liquidator chooses which to liquidate, **Then** they can liquidate any position below the health threshold
3. **Given** a position is partially liquidated, **When** the liquidation completes, **Then** the remaining position returns to a healthy state (health factor > 1.0)
4. **Given** a healthy position (health factor > 1.0), **When** a liquidator attempts to liquidate it, **Then** the transaction is rejected

---

### User Story 4 - Withdraw Supplied Assets (Priority: P4)

A liquidity provider wants to withdraw their supplied assets from the lending pool. They can withdraw up to the amount not currently borrowed, burning their pool share tokens and receiving the underlying assets plus accrued interest.

**Why this priority**: Completes the supply-side lifecycle, but requires supply (P1) to be working. Lower priority because suppliers typically deposit for longer periods.

**Independent Test**: Can be tested by supplying assets, waiting for interest to accrue, and withdrawing to verify the user receives their principal plus interest.

**Acceptance Scenarios**:

1. **Given** a user has supplied 1.0 BTC with no borrows against it, **When** they withdraw their full position, **Then** they receive 1.0 BTC plus accrued interest
2. **Given** a user has supplied assets but 80% is currently borrowed, **When** they attempt to withdraw 50%, **Then** the transaction succeeds as it's within available liquidity
3. **Given** a user has supplied assets but 80% is currently borrowed, **When** they attempt to withdraw 100%, **Then** the transaction is rejected due to insufficient liquidity
4. **Given** a user has supplied assets, **When** they make a partial withdrawal, **Then** their remaining position continues to accrue interest

---

### User Story 5 - Update Interest Rates Based on Utilization (Priority: P5)

The protocol automatically adjusts interest rates based on pool utilization. When utilization is high (most assets borrowed), rates increase to incentivize more supply. When utilization is low, rates decrease to encourage borrowing.

**Why this priority**: Important for market efficiency but can start with fixed rates. Dynamic rates optimize capital efficiency but aren't required for basic functionality.

**Independent Test**: Can be tested by observing interest rate changes as utilization crosses different thresholds (e.g., 50%, 80%, 90% utilization).

**Acceptance Scenarios**:

1. **Given** a pool with 20% utilization, **When** utilization increases to 80%, **Then** both borrow and supply rates increase according to the interest rate model
2. **Given** a pool with 90% utilization, **When** new assets are supplied reducing utilization to 70%, **Then** rates decrease accordingly
3. **Given** multiple pools with different utilizations, **When** rates are calculated, **Then** each pool's rate reflects its own utilization independently

---

### Edge Cases

- **What happens when a user tries to borrow with zero collateral?** Transaction must be rejected as it violates LTV (Loan-to-Value) requirements.
- **What happens when two users try to update the same Reserve UTXO simultaneously?** Off-chain coordinator serializes operations; if direct user transactions conflict, only first to be mined succeeds, second fails and must retry with updated Reserve UTXO state.
- **What happens with fixed-point rounding in interest calculations?** Use floor rounding (round down) for minting aTokens to prevent over-minting; use ceiling for liquidation calculations to favor protocol safety.
- **What happens when Reserve UTXO size exceeds limits?** Initial design keeps Reserve UTXO under 320 bytes; if needed, split into multiple UTXOs or store configuration off-chain with on-chain hash commitment.
- **What happens when multiple liquidators try to liquidate the same position simultaneously?** Only the first valid liquidation transaction to be included in a block succeeds; others fail as the position UTXO is already consumed.
- **What happens when oracle price feed becomes stale or unavailable?** System should reject transactions requiring price data until fresh oracle data is available, preventing operations with incorrect prices.
- **What happens when a user tries to withdraw more than available liquidity?** Transaction is rejected; users can only withdraw up to the non-borrowed portion of the pool.
- **What happens when collateral price drops rapidly during a transaction?** The transaction validates against the oracle price at transaction creation time; if price moved significantly, the transaction may fail validation or result in immediate liquidation eligibility.
- **What happens when interest accrual causes debt to exceed collateral value?** Position becomes liquidatable; liquidators can step in to restore protocol solvency.
- **What happens when a UTXO representing a position is consumed by an invalid transaction?** The transaction fails validation and is rejected by the network; the UTXO remains unconsumed.
- **What happens with dust amounts (very small deposits/borrows)?** System should enforce minimum amounts to prevent UTXO bloat and ensure economic viability of operations.

## Requirements *(mandatory)*

### Functional Requirements

#### Core Lending Operations

- **FR-001**: System MUST allow users to supply tokenized assets (BTC, USDT) to lending pools by creating reserve position UTXOs
- **FR-002**: System MUST track each supplier's proportional share of the pool and their accrued interest
- **FR-003**: System MUST allow users to withdraw supplied assets up to the available (non-borrowed) liquidity
- **FR-004**: System MUST allow users to deposit collateral and borrow assets against it, creating debt position UTXOs
- **FR-005**: System MUST enforce LTV (Loan-to-Value) ratios for borrowing (e.g., 66.7% LTV = max borrow 66.7% of collateral value) and separate liquidation thresholds (e.g., 80% = liquidate when debt exceeds 80% of collateral value)
- **FR-006**: System MUST allow borrowers to repay debt (partial or full) and reclaim proportional collateral
- **FR-007**: System MUST calculate and track interest accrual on both supply and borrow positions over time

#### Liquidation Mechanism

- **FR-008**: System MUST calculate health factors for all debt positions based on collateral value vs debt value
- **FR-009**: System MUST allow liquidators to liquidate positions with health factor below 1.0
- **FR-010**: System MUST provide liquidators with a discount (liquidation bonus) when purchasing collateral during liquidation
- **FR-011**: System MUST ensure liquidations restore positions to healthy states or fully close them

#### UTXO State Management

- **FR-012**: System MUST represent reserve pools as state UTXOs (~320 bytes) tracking: asset_id, totalLiquidity, totalVariableDebt, liquidityIndex (RAY), variableBorrowIndex (RAY), currentLiquidityRate (RAY), currentVariableBorrowRate (RAY), reserveFactor (RAY), lastUpdateTimestamp, and flags
- **FR-013**: System MUST represent individual user positions as UTXOs: aToken holdings (fungible assets) for supply, Debt UTXOs (~128 bytes) for borrows containing owner, principal (normalized), borrowIndexAtOpen (RAY), timestamps
- **FR-014**: System MUST ensure all state transitions consume old UTXOs and create new ones atomically within a single transaction
- **FR-015**: System MUST prevent double-spending of position UTXOs through standard UTXO validation
- **FR-032**: System MUST use RAY (10^27) fixed-point precision for all indices, rates, and interest calculations
- **FR-033**: System MUST use cumulative index accounting (liquidityIndex, variableBorrowIndex) to avoid updating all user balances on each interest accrual
- **FR-034**: System MUST handle UTXO race conditions through off-chain coordinator that assembles transactions using optimistic concurrency (failed attempts retry with updated state)

#### Oracle Integration

- **FR-016**: System MUST integrate with external price oracles to obtain asset prices for collateralization calculations
- **FR-017**: System MUST validate oracle signatures and timestamps to ensure price data authenticity and freshness
- **FR-018**: System MUST reject transactions when oracle data is stale beyond acceptable threshold (e.g., 10 minutes)

#### Interest Rate Model

- **FR-019**: System MUST calculate interest rates based on pool utilization (borrowed / supplied ratio)
- **FR-020**: System MUST support configurable interest rate curves (base rate, optimal utilization, slope parameters) all expressed in RAY precision
- **FR-021**: System MUST accrue interest using formula: `indexNew = indexOld * (1 + annualRate * timeElapsed / 31536000)` where all values use RAY fixed-point
- **FR-035**: System MUST apply reserveFactor (e.g., 10% in RAY) to direct portion of interest to protocol treasury
- **FR-036**: System MUST support variable rate borrowing; stable rate borrowing is out of scope for MVP

#### Asset Support

- **FR-022**: System MUST support multiple asset types as both collateral and borrowed assets (initially tokenized BTC and USDT)
- **FR-023**: System MUST maintain separate reserve pools for each supported asset
- **FR-024**: System MUST allow cross-asset borrowing (e.g., deposit BTC, borrow USDT)

#### Formal Verification Requirements

- **FR-025**: All SimplicityHL validators MUST have formal proofs that collateralization ratios cannot be violated
- **FR-026**: All SimplicityHL validators MUST have formal proofs that total borrowed never exceeds total supplied
- **FR-027**: All SimplicityHL validators MUST have formal proofs that liquidations maintain protocol solvency
- **FR-028**: All state transitions MUST be formally verified to prevent fund loss or unauthorized access

#### Testnet Deployment

- **FR-029**: System MUST be deployed and tested on Liquid testnet before any mainnet consideration
- **FR-030**: System MUST provide testnet faucets or mechanisms for obtaining test tokens for testing
- **FR-031**: System MUST log all state transitions for testnet monitoring and debugging

### Assumptions

- Liquid Network provides reliable asset issuance and transfer mechanisms for tokenized BTC and USDT
- External price oracles are available and provide signed price feeds with reasonable latency (<1 minute)
- Users have access to Liquid-compatible wallets that can construct and sign UTXO transactions
- **Off-chain coordinator service** (relayer/pool manager) will assemble transactions to handle UTXO race conditions - users submit intents, coordinator builds valid transactions
- SimplicityHL tooling and formal verification frameworks are available for development
- Testnet has sufficient liquidity and participants for realistic testing scenarios
- **Non-confidential UTXOs** will be used for MVP - confidential transactions add complexity to price validation and accounting
- **RAY precision (10^27)** is supported for fixed-point arithmetic in SimplicityHL
- UTXO size limits allow storing Reserve state (~320 bytes) and Debt positions (~128 bytes)

### Key Entities

- **Reserve Pool**: Represents the total liquidity for a specific asset (e.g., BTC pool, USDT pool). Tracks total supplied, total borrowed, liquidityIndex (RAY), variableBorrowIndex (RAY), current interest rates, reserveFactor, and utilization ratio. Implemented as a state UTXO (~320 bytes) that gets consumed and recreated with each operation. Uses cumulative index accounting to avoid updating all user balances on each accrual.

- **Supply Position (aToken)**: Represents a user's supplied assets via aToken holdings. aToken amount remains constant while value increases through liquidityIndex. Formula: `underlyingValue = aTokenAmount * liquidityIndex / RAY`. When depositing X underlying, user receives `aTokenAmount = X * RAY / liquidityIndex`. On withdrawal, burns aTokens and receives `underlying = aTokenAmount * liquidityIndex / RAY`. Implemented as fungible asset issuance or balance UTXO.

- **Debt Position**: Represents a user's borrowed amount using normalized principal. Tracks: principal (normalized), borrowIndexAtOpen (RAY), collateral references, owner pubkey hash, and timestamps. Current debt calculated as: `currentDebt = principal * variableBorrowIndex / borrowIndexAtOpen`. Implemented as a UTXO (~128 bytes) consumed and recreated on repay/liquidation. Health factor computed on-demand using oracle prices.

- **Oracle Price Feed**: External data source providing asset prices with cryptographic signatures. Contains asset pair (e.g., BTC/USD), price, timestamp, and signature. Referenced by transactions but not stored as UTXOs.

- **Interest Rate Model**: Configuration parameters defining how interest rates change with utilization. Contains base rate, optimal utilization target, slope before optimal, slope after optimal (all in RAY). Interest accrues via: `indexNew = indexOld * (1 + rate * timeElapsed / secondsPerYear)` where rate is annual rate in RAY and secondsPerYear = 31,536,000. Stored in reserve pool state or computed off-chain and validated on-chain.

- **Liquidation Event**: Record of a liquidation transaction. Contains liquidated position ID, liquidator address, collateral amount seized, debt amount cleared, liquidation bonus paid. Logged in transaction outputs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully supply assets to a pool and withdraw them with accrued interest within 3 transactions (supply, wait, withdraw) on testnet
- **SC-002**: Users can successfully borrow against collateral and repay loans within 4 transactions (deposit collateral, borrow, repay, withdraw collateral) on testnet
- **SC-003**: Liquidators can successfully liquidate undercollateralized positions within 1 transaction when health factor drops below 1.0
- **SC-004**: System maintains 100% solvency - total borrowed never exceeds total supplied across all pools, verified through formal proofs
- **SC-005**: Interest accrual calculations are accurate to within 0.01% of expected values based on time elapsed and interest rate
- **SC-006**: All core operations (supply, withdraw, borrow, repay, liquidate) complete within 2 block confirmations on Liquid testnet
- **SC-007**: System handles at least 10 concurrent users performing different operations without state conflicts or double-spends
- **SC-008**: Oracle price updates are reflected in health factor calculations within 1 block of price feed update
- **SC-009**: Formal verification proofs validate all critical invariants (collateralization, solvency, no fund loss) with 100% coverage
- **SC-010**: System successfully operates on Liquid testnet for at least 30 days with multiple users and various market conditions without critical failures
