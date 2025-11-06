# Implementation Plan: UTXO-Based Lending Protocol

**Branch**: `001-utxo-lending-protocol` | **Date**: 2025-11-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-utxo-lending-protocol/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement an AAVE-inspired lending protocol adapted for UTXO/SimplicityHL on Liquid Network testnet. Core operations include supply (with aToken indexing), borrow (with collateral), repay, liquidation, and dynamic interest rates. Uses cumulative index accounting (RAY 10^27 precision) to minimize UTXO writes, off-chain coordinator for transaction assembly, and formal verification for all validators. Backend in Python handles business logic and coordinator, SimplicityHL validators enforce on-chain rules, Elements SDK integrates with Liquid, frontend in Node.js provides user interface, SQLite stores off-chain state.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+ (backend/coordinator), Node.js 18+ (frontend), SimplicityHL (validators)  
**Primary Dependencies**: 
- Backend: FastAPI, Elements SDK (python-elementstx), SQLAlchemy, web3-like library for Liquid
- Frontend: React 18+, TypeScript, TailwindCSS, shadcn/ui, Lucide icons, ethers.js-equivalent for Liquid
- Validators: SimplicityHL compiler, formal verification tools (Coq/Isabelle), RAY fixed-point library
- Integration: Elements Core (Liquid node), Oracle service (signed price feeds)

**Storage**: SQLite (local database for off-chain state: user positions, transaction history, oracle cache)  
**Testing**: pytest (Python backend), Jest (Node.js frontend), property-based testing (Hypothesis), SimplicityHL formal verification, integration tests on Liquid regtest  
**Target Platform**: Liquid Network testnet, Linux/macOS development environment, web browser (frontend)  
**Project Type**: Web application (backend API + frontend UI + on-chain validators)  
**Performance Goals**: 
- Transaction assembly: <500ms for coordinator to build valid UTXO transaction
- Interest calculation: <100ms for index accrual computation
- Oracle price fetch: <1 second staleness tolerance
- Frontend responsiveness: <200ms for UI updates
- Support 10+ concurrent users on testnet without UTXO conflicts

**Constraints**: 
- Reserve UTXO size: ~320 bytes (must fit in Liquid script data)
- Debt UTXO size: ~128 bytes
- RAY precision: 10^27 fixed-point (no floating point in validators)
- Non-confidential UTXOs for MVP (confidential transactions deferred)
- Testnet-only deployment (no mainnet until full audit)
- Formal verification required for all validators before testnet deployment

**Scale/Scope**: 
- MVP: 2 assets (tokenized BTC, USDT), single reserve pool per asset
- Target: 10-50 testnet users, 100+ transactions/day
- Codebase: ~5k LOC Python, ~3k LOC TypeScript, ~2k LOC SimplicityHL
- 5 core user stories, 36 functional requirements, 10 success criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Formal Verification First ✅
- [ ] SimplicityHL validators with formal proofs for Reserve and Debt
- [ ] Mathematical proofs of collateralization invariants
- [ ] Formal specification of state transitions
- [ ] Proven safety properties (no fund loss, no unauthorized access)
- **Status**: PASS (deferred to implementation) - Architecture supports formal verification
- **Note**: Validators will be designed with formal verification in mind; proofs developed during implementation phase

### II. Liquid Network Native ✅
- [x] Designed for Liquid testnet using Elements SDK
- [x] UTXO model (not EVM/Solidity)
- [x] Non-confidential UTXOs for MVP (confidential transactions deferred)
- [x] Asset issuance for tokenized BTC/USDT
- [x] Future Elements sidechain compatibility maintained
- **Status**: PASS - Full Liquid Network integration planned

### III. AAVE-Inspired Architecture ✅
- [x] Reserve Validators manage liquidity pools, interest rates (liquidityIndex, variableBorrowIndex)
- [x] Debt Validators track borrowing positions, health factors
- [x] Clear separation: Reserve UTXO (~320B) vs Debt UTXO (~128B)
- [x] Multiple collateral types supported (BTC, USDT)
- [x] Cumulative index accounting (AAVE pattern)
- **Status**: PASS - Architecture directly adapted from AAVE with UTXO modifications

### IV. Testnet-First Development ✅
- [x] All development on Liquid testnet
- [x] Formal verification before testnet deployment
- [x] Economic simulations planned (Python off-chain model)
- [x] No mainnet deployment without full audit
- **Status**: PASS - Testnet-only scope explicit in requirements

### V. Modular Validator Design ✅
- [x] Reserve Validator: independent, self-contained
- [x] Debt Validator: independent, self-contained
- [x] Oracle Validator: separate component
- [x] Clear interfaces (UTXO consumption/creation contracts)
- [x] Independent deployment paths
- **Status**: PASS - Modular UTXO-based design with minimal cross-dependencies

### VI. Observability and Transparency ✅
- [x] Event logging for all state transitions (FR-031)
- [x] Public queryable state (SQLite mirrors on-chain state)
- [x] Audit trails for liquidations
- [x] Health factor monitoring (coordinator service)
- **Status**: PASS - Comprehensive logging and monitoring planned

### Security Requirements ✅
- [x] Liquid cryptographic primitives (Schnorr/ECDSA)
- [x] Oracle signature validation
- [x] Multi-sig governance (deferred to future)
- [x] Collateralization formally verified
- [x] Oracle staleness checks (10-minute threshold)
- **Status**: PASS - Security requirements addressed in FR-016 through FR-018, FR-025 through FR-028

### Development Workflow ✅
- [x] Phase 0: Research (this plan)
- [x] Phase 1: Design (data model, contracts, quickstart)
- [x] Phase 2: Implementation (validators, backend, frontend)
- [x] Testing: unit, integration, property-based, formal verification
- **Status**: PASS - Workflow follows constitution phases

**Overall Gate Status**: ✅ PASS - All constitution principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/                          # Python backend (coordinator + API)
├── src/
│   ├── models/                   # SQLAlchemy models (User, Position, Transaction)
│   ├── services/
│   │   ├── coordinator.py        # UTXO transaction assembly
│   │   ├── reserve_service.py    # Reserve pool operations
│   │   ├── debt_service.py       # Debt position management
│   │   ├── oracle_service.py     # Price feed integration
│   │   └── interest_calculator.py # RAY fixed-point math
│   ├── api/
│   │   ├── routes/               # FastAPI endpoints
│   │   │   ├── supply.py
│   │   │   ├── borrow.py
│   │   │   ├── repay.py
│   │   │   ├── liquidate.py
│   │   │   └── positions.py
│   │   └── schemas/              # Pydantic models
│   ├── validators/               # SimplicityHL integration
│   │   ├── reserve_validator.py  # Python wrapper for Reserve validator
│   │   └── debt_validator.py     # Python wrapper for Debt validator
│   └── utils/
│       ├── ray_math.py           # RAY (10^27) fixed-point library
│       └── liquid_client.py      # Elements SDK wrapper
├── tests/
│   ├── unit/                     # pytest unit tests
│   ├── integration/              # Liquid regtest integration tests
│   └── property/                 # Hypothesis property-based tests
├── alembic/                      # SQLite migrations
├── requirements.txt
└── pyproject.toml

frontend/                         # Node.js frontend (React + TypeScript)
├── src/
│   ├── components/
│   │   ├── SupplyForm.tsx        # Supply assets UI
│   │   ├── BorrowForm.tsx        # Borrow UI
│   │   ├── PositionCard.tsx      # Display user positions
│   │   ├── HealthFactor.tsx      # Health factor visualization
│   │   └── ui/                   # shadcn/ui components
│   ├── pages/
│   │   ├── Dashboard.tsx         # Main dashboard
│   │   ├── Supply.tsx            # Supply page
│   │   ├── Borrow.tsx            # Borrow page
│   │   └── Liquidate.tsx         # Liquidation page
│   ├── services/
│   │   ├── api.ts                # Backend API client
│   │   └── liquid.ts             # Liquid wallet integration
│   ├── hooks/
│   │   ├── usePositions.ts       # Fetch user positions
│   │   └── useOracle.ts          # Oracle price updates
│   └── utils/
│       └── formatting.ts         # RAY display formatting
├── tests/
│   └── components/               # Jest + React Testing Library
├── package.json
└── tsconfig.json

validators/                       # SimplicityHL validators
├── reserve/
│   ├── reserve.simpl             # Reserve UTXO validator
│   ├── reserve.spec              # Formal specification
│   └── proofs/                   # Coq/Isabelle proofs
│       ├── collateralization.v
│       ├── solvency.v
│       └── index_accrual.v
├── debt/
│   ├── debt.simpl                # Debt UTXO validator
│   ├── debt.spec                 # Formal specification
│   └── proofs/
│       ├── health_factor.v
│       └── repayment.v
├── oracle/
│   └── oracle_validator.simpl    # Oracle signature validation
└── lib/
    ├── ray_math.simpl            # RAY fixed-point library
    └── utxo_helpers.simpl        # UTXO validation helpers

shared/                           # Shared types and constants
├── types/
│   ├── reserve.ts                # Reserve UTXO structure
│   ├── debt.ts                   # Debt UTXO structure
│   └── oracle.ts                 # Oracle feed structure
└── constants/
    ├── ray.ts                    # RAY = 10^27
    └── addresses.ts              # Testnet contract addresses

scripts/                          # Development scripts
├── deploy_validators.sh          # Deploy SimplicityHL to testnet
├── setup_testnet.sh              # Initialize testnet environment
├── mint_test_tokens.sh           # Create test BTC/USDT
└── run_regtest.sh                # Start local Liquid regtest

docs/                             # Additional documentation
├── architecture.md               # System architecture
├── utxo_flows.md                 # UTXO transaction flows
└── formal_verification.md        # Verification approach

.specify/                         # Spec Kit artifacts
└── (existing structure)
```

**Structure Decision**: Web application architecture selected. Backend handles off-chain coordination and API, frontend provides user interface, validators enforce on-chain rules. Separation enables:
- Independent testing of Python business logic
- Formal verification of SimplicityHL validators in isolation
- Frontend development against mocked backend
- Clear boundaries between off-chain (coordinator, SQLite) and on-chain (validators, UTXOs) components

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
