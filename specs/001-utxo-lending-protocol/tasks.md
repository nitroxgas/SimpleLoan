# Tasks: UTXO-Based Lending Protocol

**Input**: Design documents from `/specs/001-utxo-lending-protocol/`  
**Branch**: `001-utxo-lending-protocol`  
**Date**: 2025-11-06

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US5) this task belongs to
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/src/`
- Frontend: `frontend/src/`
- Validators: `validators/`
- Shared: `shared/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend directory structure (src/models, src/services, src/api, src/utils, src/validators, tests/)
- [x] T002 Create frontend directory structure (src/components, src/pages, src/services, src/hooks, src/utils, tests/)
- [x] T003 Create validators directory structure (reserve/, debt/, oracle/, lib/)
- [x] T004 Create shared directory structure (types/, constants/)
- [x] T005 [P] Initialize Python backend with requirements.txt (FastAPI, SQLAlchemy, Elements SDK, pytest, Hypothesis)
- [x] T006 [P] Initialize Node.js frontend with package.json (React, TypeScript, TailwindCSS, shadcn/ui)
- [x] T007 [P] Configure Python linting (black, flake8, mypy) in backend/pyproject.toml
- [x] T008 [P] Configure TypeScript strict mode and ESLint in frontend/tsconfig.json
- [x] T009 [P] Setup Git hooks for pre-commit checks in .git/hooks/pre-commit

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Setup SQLite database schema in backend/alembic/versions/001_initial_schema.py
- [x] T011 Create base SQLAlchemy models (Base, TimestampMixin) in backend/src/models/base.py
- [x] T012 [P] Implement RAY fixed-point math library in backend/src/utils/ray_math.py (RAY=10^27, ray_mul, ray_div, accrue_index)
- [x] T013 [P] Implement Elements/Liquid client wrapper in backend/src/utils/liquid_client.py (RPC calls, UTXO fetching, tx broadcast)
- [x] T014 [P] Create shared TypeScript types for Reserve UTXO in shared/types/reserve.ts
- [x] T015 [P] Create shared TypeScript types for Debt UTXO in shared/types/debt.ts
- [x] T016 [P] Create shared TypeScript types for Oracle feed in shared/types/oracle.ts
- [x] T017 [P] Define RAY constant in shared/constants/ray.ts
- [x] T018 Setup FastAPI application with CORS in backend/src/main.py
- [x] T019 [P] Implement error handling middleware in backend/src/api/middleware/error_handler.py
- [x] T020 [P] Implement logging configuration in backend/src/utils/logger.py
- [x] T021 [P] Setup environment configuration in backend/src/config.py (.env loading, validation)
- [x] T022 Create User model in backend/src/models/user.py (id, created_at, health_factor)
- [x] T023 Create ReserveState model in backend/src/models/reserve_state.py (asset_id, utxo_id, indices, rates, timestamps)
- [x] T024 Run Alembic migrations to create database tables: alembic upgrade head

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Supply Assets to Lending Pool (Priority: P1) 🎯 MVP

**Goal**: Enable users to supply tokenized BTC/USDT to lending pools and receive aTokens that accrue interest

**Independent Test**: Supply 1.0 BTC → receive aTokens → wait for interest accrual → verify aToken value increased → withdraw → receive BTC + interest

### Implementation for User Story 1

- [x] T025 [P] [US1] Create SupplyPosition model in backend/src/models/supply_position.py (id, user_id, asset_id, atoken_amount, timestamps)
- [x] T026 [P] [US1] Implement interest calculator service in backend/src/services/interest_calculator.py (accrue_index, calculate_atoken_amount)
- [x] T027 [US1] Implement ReserveService for supply operations in backend/src/services/reserve_service.py (supply, update_indices, get_reserve_state)
- [x] T028 [US1] Create supply intent schema in backend/src/api/schemas/supply.py (Pydantic models for SupplyIntent, WithdrawIntent)
- [x] T029 [US1] Implement POST /api/v1/supply endpoint in backend/src/api/routes/supply.py (accept intent, validate, queue for coordinator)
- [x] T030 [US1] Implement GET /api/v1/positions/{user_id} endpoint in backend/src/api/routes/positions.py (fetch user supply positions)
- [x] T031 [US1] Implement coordinator service for supply in backend/src/services/coordinator.py (assemble supply transaction, handle UTXO locks)
- [x] T032 [P] [US1] Create SupplyForm component in frontend/src/components/SupplyForm.tsx (amount input, asset selector, submit button)
- [x] T033 [P] [US1] Create PositionCard component in frontend/src/components/PositionCard.tsx (display aToken balance, underlying value)
- [x] T034 [P] [US1] Implement usePositions hook in frontend/src/hooks/usePositions.ts (fetch and cache user positions)
- [x] T035 [US1] Create Supply page in frontend/src/pages/Supply.tsx (integrate SupplyForm, show current positions)
- [x] T036 [US1] Implement API client for supply in frontend/src/services/api.ts (POST /supply, GET /positions)
- [x] T037 [US1] Add supply operation logging in backend/src/services/reserve_service.py

**Checkpoint**: At this point, users can supply assets and receive aTokens. Test independently before proceeding.

---

## Phase 4: User Story 2 - Borrow Against Collateral (Priority: P2)

**Goal**: Enable users to borrow assets by providing collateral, with health factor tracking

**Independent Test**: Deposit 2.0 BTC collateral → borrow $50k USDT → verify debt position created → repay loan → reclaim collateral

### Implementation for User Story 2

- [x] T038 [P] [US2] Create DebtPosition model in backend/src/models/debt_position.py (id, user_id, borrowed_asset_id, collateral_asset_id, principal, borrow_index_at_open)
- [x] T039 [P] [US2] Implement OracleService in backend/src/services/oracle_service.py (fetch prices, verify signatures, check staleness)
- [x] T040 [US2] Implement DebtService in backend/src/services/debt_service.py (borrow, calculate_health_factor, repay)
- [x] T041 [US2] Create borrow intent schema in backend/src/api/schemas/borrow.py (BorrowIntent, RepayIntent)
- [x] T042 [US2] Implement POST /api/v1/borrow endpoint in backend/src/api/routes/borrow.py (validate collateral, check health factor, queue)
- [x] T043 [US2] Implement POST /api/v1/repay endpoint in backend/src/api/routes/repay.py (partial or full repayment)
- [x] T044 [US2] Extend coordinator for borrow operations in backend/src/services/coordinator.py (assemble borrow tx, validate LTV)
- [x] T045 [P] [US2] Create BorrowForm component in frontend/src/components/BorrowForm.tsx (collateral input, borrow amount, LTV display)
- [x] T046 [P] [US2] Create HealthFactor component in frontend/src/components/HealthFactor.tsx (visual health factor gauge)
- [x] T047 [P] [US2] Implement useOracle hook in frontend/src/hooks/useOracle.ts (fetch and display current prices)
- [x] T048 [US2] Create Borrow page in frontend/src/pages/Borrow.tsx (integrate BorrowForm, show debt positions, health factors)
- [x] T049 [US2] Implement API client for borrow in frontend/src/services/api.ts (POST /borrow, POST /repay)
- [x] T050 [US2] Add health factor calculation in backend/src/services/debt_service.py (collateral_value * threshold / debt_value)

**Checkpoint**: Users can borrow against collateral and repay loans. Test independently.

---

## Phase 5: User Story 3 - Liquidate Undercollateralized Positions (Priority: P3)

**Goal**: Enable liquidators to liquidate unhealthy positions and maintain protocol solvency

**Independent Test**: Create undercollateralized position (simulate price drop) → liquidator submits liquidation → verify collateral seized, debt cleared

### Implementation for User Story 3

- [x] T051 [P] [US3] Implement liquidation logic in backend/src/services/debt_service.py (liquidate, calculate_liquidation_bonus, validate_health_factor)
- [x] T052 [US3] Create liquidation intent schema in backend/src/api/schemas/liquidate.py (LiquidateIntent)
- [x] T053 [US3] Implement POST /api/v1/liquidate endpoint in backend/src/api/routes/liquidate.py (validate position unhealthy, queue liquidation)
- [x] T054 [US3] Implement GET /api/v1/positions/liquidatable endpoint in backend/src/api/routes/positions.py (query positions with health_factor < 1.0)
- [x] T055 [US3] Extend coordinator for liquidation in backend/src/services/coordinator.py (assemble liquidation tx, transfer collateral to liquidator)
- [x] T056 [P] [US3] Create Liquidate page in frontend/src/pages/Liquidate.tsx (list liquidatable positions, liquidation form)
- [x] T057 [US3] Implement API client for liquidation in frontend/src/services/api.ts (POST /liquidate, GET /positions/liquidatable)
- [x] T058 [US3] Add liquidation event logging in backend/src/services/debt_service.py

**Checkpoint**: Liquidators can liquidate unhealthy positions. Protocol solvency maintained.

---

## Phase 6: User Story 4 - Withdraw Supplied Assets (Priority: P4)

**Goal**: Complete supply-side lifecycle by enabling withdrawals

**Independent Test**: Supply 1.0 BTC → wait for interest → withdraw full balance → verify received principal + interest

### Implementation for User Story 4

- [x] T059 [US4] Implement withdraw logic in backend/src/services/reserve_service.py (withdraw, check_available_liquidity, burn_atokens)
- [x] T060 [US4] Implement POST /api/v1/withdraw endpoint in backend/src/api/routes/supply.py (validate liquidity, queue withdrawal)
- [x] T061 [US4] Extend coordinator for withdraw in backend/src/services/coordinator.py (assemble withdraw tx, burn aTokens, transfer underlying)
- [x] T062 [P] [US4] Add withdraw functionality to Supply page in frontend/src/pages/Supply.tsx (withdraw button, amount input)
- [x] T063 [US4] Implement API client for withdraw in frontend/src/services/api.ts (POST /withdraw)

**Checkpoint**: Users can withdraw supplied assets. Supply lifecycle complete.

---

## Phase 7: User Story 5 - Update Interest Rates Based on Utilization (Priority: P5)

**Goal**: Implement dynamic interest rate model based on pool utilization

**Independent Test**: Observe interest rate changes as utilization crosses thresholds (50%, 80%, 90%)

### Implementation for User Story 5

- [x] T064 [P] [US5] Implement interest rate model in backend/src/services/interest_rate_model.py (calculate_rates, optimal_utilization, slope1, slope2)
- [x] T065 [US5] Integrate rate model into ReserveService in backend/src/services/reserve_service.py (update rates on each operation)
- [x] T066 [US5] Implement GET /api/v1/reserves endpoint in backend/src/api/routes/reserves.py (fetch all reserve states with current rates)
- [x] T067 [US5] Implement GET /api/v1/reserves/{asset_id} endpoint in backend/src/api/routes/reserves.py (fetch specific reserve state)
- [x] T068 [P] [US5] Create Dashboard page in frontend/src/pages/Dashboard.tsx (display all reserves, utilization, rates)
- [x] T069 [US5] Implement API client for reserves in frontend/src/services/api.ts (GET /reserves)

**Checkpoint**: Interest rates adjust dynamically based on utilization.

---

## Phase 8: SimplicityHL Validators (Formal Verification)

**Purpose**: Implement and verify on-chain validators

- [x] T070 [P] Define Reserve UTXO binary layout in docs/validators/reserve-utxo-layout.md (320 bytes, field offsets)
- [x] T071 [P] Define Debt UTXO binary layout in docs/validators/debt-utxo-layout.md (128 bytes, field offsets)
- [x] T072 [P] RAY math library specification in docs/validators/ray-math-spec.md (ray_mul, ray_div, accrue_index)
- [x] T073 Reserve validator specification (awaiting SimplicityHL toolchain)
- [x] T074 Debt validator specification (awaiting SimplicityHL toolchain)
- [x] T075 [P] Oracle validator specification (awaiting SimplicityHL toolchain)
- [x] T076 [P] Coq proof sketch for solvency invariant in docs/validators/coq-proofs-sketch.md
- [x] T077 [P] Coq proof sketch for index monotonicity in docs/validators/coq-proofs-sketch.md
- [x] T078 [P] Coq proof sketch for health factor in docs/validators/coq-proofs-sketch.md
- [x] T079 Compilation instructions documented (awaiting toolchain)
- [x] T080 Verification instructions documented (awaiting Coq implementation)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T081 [P] Write property-based tests for RAY math in backend/tests/property/test_ray_math.py (Hypothesis: commutativity, monotonicity)
- [ ] T082 [P] Write integration tests for supply flow in backend/tests/integration/test_supply.py (regtest: supply → accrue → withdraw)
- [ ] T083 [P] Write integration tests for borrow flow in backend/tests/integration/test_borrow.py (regtest: borrow → repay)
- [ ] T084 [P] Write integration tests for liquidation in backend/tests/integration/test_liquidate.py (regtest: create unhealthy → liquidate)
- [ ] T085 [P] Write frontend component tests in frontend/tests/components/ (Jest + React Testing Library)
- [x] T086 [P] Add API documentation comments in backend/src/api/routes/ (OpenAPI docstrings)
- [ ] T087 [P] Implement rate limiting middleware in backend/src/api/middleware/rate_limiter.py (60 req/min per user)
- [x] T088 [P] Add transaction history tracking in backend/src/models/transaction.py (audit log)
- [ ] T089 [P] Implement oracle price caching in backend/src/models/oracle_price.py (reduce RPC calls)
- [ ] T090 [P] Add performance monitoring in backend/src/utils/metrics.py (track coordinator latency)
- [x] T091 Update README.md with setup instructions and architecture diagram
- [x] T092 Create deployment scripts in scripts/ (deploy_validators.sh, setup_testnet.sh, mint_test_tokens.sh)
- [ ] T093 Run full quickstart.md validation on clean environment
- [ ] T094 Security audit checklist: verify no secrets in code, validate all inputs, check SQL injection prevention
- [ ] T095 Code cleanup: remove TODOs, add missing docstrings, format with black/prettier

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational completion
  - US1 (Supply): Can start after Foundational
  - US2 (Borrow): Can start after Foundational (integrates with US1 but independently testable)
  - US3 (Liquidate): Can start after Foundational (requires US1+US2 concepts but independently testable)
  - US4 (Withdraw): Can start after Foundational (completes US1 lifecycle)
  - US5 (Interest Rates): Can start after Foundational (enhances all stories)
- **Validators (Phase 8)**: Can proceed in parallel with user stories
- **Polish (Phase 9)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent - can complete alone for MVP
- **US2 (P2)**: Independent - uses oracle and debt models
- **US3 (P3)**: Independent - uses liquidation logic
- **US4 (P4)**: Extends US1 - completes supply lifecycle
- **US5 (P5)**: Enhances all - dynamic rates

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Validators and Coq proofs can be developed in parallel with backend/frontend

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T024) - CRITICAL
3. Complete Phase 3: User Story 1 (T025-T037)
4. **STOP and VALIDATE**: Test supply → accrue → withdraw flow
5. Deploy to regtest and demo

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy (MVP!)
3. Add US2 → Test independently → Deploy
4. Add US3 → Test independently → Deploy
5. Add US4 → Test independently → Deploy
6. Add US5 → Test independently → Deploy
7. Add Validators → Formal verification complete
8. Polish → Production ready

### Parallel Team Strategy

With 3 developers:

1. Team completes Setup + Foundational together (T001-T024)
2. Once Foundational done:
   - Developer A: US1 Supply (T025-T037)
   - Developer B: US2 Borrow (T038-T050)
   - Developer C: Validators (T070-T080)
3. Stories integrate and test independently

---

## Task Summary

**Total Tasks**: 95
- Setup: 9 tasks
- Foundational: 15 tasks (BLOCKING)
- US1 (Supply): 13 tasks
- US2 (Borrow): 13 tasks
- US3 (Liquidate): 8 tasks
- US4 (Withdraw): 5 tasks
- US5 (Interest Rates): 6 tasks
- Validators: 11 tasks
- Polish: 15 tasks

**Parallel Opportunities**: 45 tasks marked [P]

**MVP Scope**: Phase 1 (9) + Phase 2 (15) + Phase 3 (13) = **37 tasks**

**Independent Test Criteria**:
- US1: Supply → wait → withdraw with interest ✅
- US2: Deposit collateral → borrow → repay → reclaim ✅
- US3: Create unhealthy position → liquidate ✅
- US4: Supply → withdraw (completes US1) ✅
- US5: Observe rate changes with utilization ✅

---

## Notes

- [P] = Parallelizable (different files, no blocking dependencies)
- [US#] = User story label for traceability
- Each user story independently completable and testable
- Stop at any checkpoint to validate story
- Commit after each task or logical group
- Follow constitution: formal verification, testnet-first, modular design
