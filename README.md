# Billau

> **AAVE-inspired lending protocol with formal verification on Liquid Network**
# Fantasma Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Network: Liquid](https://img.shields.io/badge/Network-Liquid-blue.svg)](https://liquid.net/)
[![Language: SimplicityHL](https://img.shields.io/badge/Language-SimplicityHL-green.svg)](https://github.com/BlockstreamResearch/simplicity)
[![Status: Development](https://img.shields.io/badge/Status-Development-orange.svg)]()
[![Progress: 92%](https://img.shields.io/badge/Progress-92%25-brightgreen.svg)]()
[![LOC: 18K](https://img.shields.io/badge/LOC-18K-blue.svg)]()

> **AAVE-inspired lending protocol with formal verification on Liquid Network**

Billau is a decentralized lending protocol that brings AAVE's battle-tested architecture to Bitcoin's Liquid sidechain using formally verified smart contracts. Built with SimplicityHL and adapted for the UTXO model, Billau enables users to supply assets, borrow against collateral, and participate in a trustless lending market with mathematical guarantees of correctness.

---

## 🎯 Project Objectives

1. **Formal Verification First**: All smart contract logic is mathematically proven correct before deployment
2. **Bitcoin-Native DeFi**: Leverage Liquid Network's Bitcoin security with enhanced privacy and asset issuance
3. **UTXO Innovation**: Adapt proven EVM lending patterns to UTXO architecture with cumulative index accounting
4. **Institutional Grade**: Provide lending infrastructure suitable for institutional adoption with formal guarantees
5. **Open Source**: Build transparent, auditable, community-driven financial infrastructure

---

## ✨ Core Features

### 🏦 Lending Operations

- **Supply Assets**: Deposit tokenized BTC, USDT, or other Liquid assets to earn interest
- **Borrow Against Collateral**: Take loans using supplied assets as collateral with configurable LTV ratios
- **Dynamic Interest Rates**: Market-driven rates based on pool utilization (AAVE's interest rate model)
- **Cross-Asset Borrowing**: Deposit BTC, borrow USDT (or any supported asset pair)
- **Flexible Repayment**: Partial or full repayment with automatic interest accrual

### 🛡️ Safety & Liquidation

- **Health Factor Monitoring**: Real-time tracking of position safety (collateral value vs. debt)
- **Automated Liquidation**: Liquidators can close undercollateralized positions to protect protocol solvency
- **Liquidation Bonus**: Incentivize liquidators with discounted collateral (e.g., 5% bonus)
- **Oracle Integration**: Signed price feeds with staleness checks (10-minute threshold)

### 🔬 Formal Verification

- **SimplicityHL Validators**: All on-chain logic written in formally verifiable language
- **Mathematical Proofs**: Coq proofs for critical invariants (solvency, collateralization, index monotonicity)
- **Proven Safety Properties**: No fund loss, no unauthorized access, bounded interest accrual
- **Independent Verification**: Modular validators can be verified in isolation

### 💎 UTXO-Specific Innovations

- **Cumulative Index Accounting**: aToken value grows via liquidityIndex (RAY 10^27 precision) without updating all balances
- **State UTXOs**: Reserve pools and debt positions represented as consumable/creatable UTXOs
- **Atomic State Transitions**: All operations consume old state and create new state in single transaction
- **Off-Chain Coordinator**: Handles UTXO race conditions with optimistic concurrency and transaction assembly

---

## 🏗️ Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TS)                    │
│  Dashboard │ Supply │ Borrow │ Repay │ Liquidate │ Positions │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│              Backend (Python + FastAPI)                      │
│  Coordinator │ Services │ API Routes │ Oracle Integration    │
└─────────────────────┬───────────────────────────────────────┘
                      │ Elements SDK
┌─────────────────────▼───────────────────────────────────────┐
│                  Liquid Network (Testnet)                    │
│  Reserve UTXOs │ Debt UTXOs │ aTokens │ Oracle Signatures    │
└─────────────────────┬───────────────────────────────────────┘
                      │ Validates
┌─────────────────────▼───────────────────────────────────────┐
│           SimplicityHL Validators (Formally Verified)        │
│  Reserve Validator │ Debt Validator │ Oracle Validator       │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Smart Contracts**:
- **SimplicityHL**: Formally verifiable smart contract language
- **Coq**: Theorem prover for mathematical correctness proofs
- **Elements/Liquid**: Bitcoin sidechain with asset issuance and confidential transactions

**Backend**:
- **Python 3.11+**: Backend coordinator and API server
- **FastAPI**: Modern async web framework with OpenAPI
- **SQLAlchemy**: ORM for off-chain state management
- **SQLite**: Local database for position tracking and caching
- **Elements SDK**: Python bindings for Liquid Network integration

**Frontend**:
- **React 18**: Modern UI framework with hooks
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **shadcn/ui**: Beautiful, accessible component library
- **Lucide Icons**: Modern icon set

**Testing**:
- **pytest**: Python unit and integration tests
- **Hypothesis**: Property-based testing for invariants
- **Jest**: Frontend component testing
- **Formal Verification**: Coq proofs for validators

---

## 🚀 Quick Start

### Prerequisites

**Required**:
- Python 3.11+
- Node.js 18+
- Git

**Optional** (for validators):
- Elements Core (Liquid node)
- SimplicityHL compiler (`simc`)
- Coq proof assistant

### Quick Commands

```bash
# Setup testnet environment (automated)
./scripts/setup_testnet.sh

# Mint test tokens
./scripts/mint_test_tokens.sh

# Start backend API
cd backend && uvicorn src.main:app --reload

# Start frontend
cd frontend && npm start

# View API docs
# http://localhost:8000/docs

# Compile validators
./scripts/compile_validators.sh

# Verify proofs
./scripts/verify_proofs.sh

# Deploy validators
./scripts/deploy_validators.sh
```

### Installation

```bash
# Clone repository
git clone https://github.com/nitroxgas/SimpleLoan.git billau
cd billau

# Setup Elements regtest node
./scripts/setup_testnet.sh

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Setup frontend
cd ../frontend
npm install

# Start development servers
# Terminal 1: Elements node
elementsd -regtest

# Terminal 2: Backend
cd backend && uvicorn src.main:app --reload

# Terminal 3: Frontend
cd frontend && npm start
```

For detailed setup instructions, see [Quickstart Guide](specs/001-utxo-lending-protocol/quickstart.md).

---

## 📁 Project Structure

```
fantasma/
├── validators/              # SimplicityHL validators & Coq proofs
│   ├── lib/                # RAY math library
│   ├── reserve/            # Reserve validator + solvency proofs
│   ├── debt/               # Debt validator + health factor proofs
│   └── oracle/             # Oracle validator
│
├── backend/                # Python FastAPI backend
│   ├── src/
│   │   ├── api/           # REST API routes & schemas
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic services
│   │   └── utils/         # RAY math, Liquid client, logger
│   └── alembic/           # Database migrations
│
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/         # Dashboard, Supply, Borrow, Liquidate
│   │   ├── components/    # Reusable UI components
│   │   ├── hooks/         # Custom React hooks
│   │   └── services/      # API client
│
├── scripts/                # Deployment & setup scripts
│   ├── setup_testnet.sh   # Automated testnet setup
│   ├── mint_test_tokens.sh# Token minting
│   ├── compile_validators.sh  # Compile SimplicityHL
│   ├── verify_proofs.sh   # Verify Coq proofs
│   └── deploy_validators.sh   # Deploy to Liquid
│
├── specs/                  # Project specifications
│   └── 001-utxo-lending-protocol/
│       ├── spec.md        # Feature specification
│       ├── plan.md        # Implementation plan
│       ├── data-model.md  # Data structures
│       ├── tasks.md       # Task breakdown
│       └── quickstart.md  # Setup guide
│
├── development_docs/       # Development notes & summaries
│   ├── PHASE_8_COMPLETE.md
│   ├── T070-T080_SUMMARY.md
│   ├── T086-T088-T091-T092_SUMMARY.md
│   └── ...
│
├── docs/                   # Additional documentation
│   └── validators/        # Validator-specific docs
│
├── shared/                 # Shared types & constants
│   ├── constants/         # RAY constants
│   └── types/             # TypeScript type definitions
│
└── .specify/              # Project metadata & archives
    └── ARCHIVE_2025-11-06.md
```

---

## 📖 Documentation

### Core Specifications
- **[Feature Specification](specs/001-utxo-lending-protocol/spec.md)**: Complete feature requirements and user stories
- **[Implementation Plan](specs/001-utxo-lending-protocol/plan.md)**: Technical architecture and design decisions
- **[Data Model](specs/001-utxo-lending-protocol/data-model.md)**: On-chain and off-chain data structures
- **[Tasks Breakdown](specs/001-utxo-lending-protocol/tasks.md)**: Detailed task list with status
- **[Quickstart Guide](specs/001-utxo-lending-protocol/quickstart.md)**: Developer setup instructions

### Validator Documentation
- **[Validator Implementation Guide](validators/IMPLEMENTATION_GUIDE.md)**: Complete guide for SimplicityHL validators
- **[Validator Quickstart](validators/QUICKSTART.md)**: Quick reference for validator compilation and deployment
- **[Validator README](validators/README.md)**: Overview of validator architecture

### API & Frontend
- **[API Documentation](http://localhost:8000/docs)**: Interactive OpenAPI/Swagger UI (when backend running)
- **[Frontend README](frontend/README.md)**: Frontend setup and architecture
- **[Frontend Troubleshooting](frontend/TROUBLESHOOTING.md)**: Common issues and solutions

### Project Status
- **[Project Status](PROJECT_STATUS_FINAL.md)**: Overall project progress and completion status
- **[Quickstart Guide](QUICKSTART.md)**: Quick start for the entire project
- **[Archive](.specify/ARCHIVE_2025-11-06.md)**: Complete project snapshot (Nov 6, 2025)

### Development Documentation
Detailed implementation notes and phase summaries are available in the [`development_docs/`](development_docs/) directory.

---

## 📊 Project Statistics

### Implementation Progress
- **Tasks Completed**: 87/95 (92%)
- **Total Lines of Code**: ~18,000 LOC
- **Files**: 117+ files across all components

### Code Breakdown
| Component | Lines of Code | Files | Status |
|-----------|---------------|-------|--------|
| SimplicityHL Validators | 2,100 | 4 | ✅ Complete |
| Coq Formal Proofs | 780 | 3 | ✅ Complete |
| Backend (Python) | ~8,000 | 50+ | ✅ Complete |
| Frontend (React/TS) | ~4,000 | 25+ | ✅ Complete |
| Scripts & Docs | ~3,000 | 35+ | ✅ Complete |

### Phase Completion
| Phase | Tasks | Progress |
|-------|-------|----------|
| 1. Setup | 9/9 | 100% ✅ |
| 2. Foundational | 15/15 | 100% ✅ |
| 3. Supply | 13/13 | 100% ✅ |
| 4. Borrow | 10/10 | 100% ✅ |
| 5. Liquidate | 8/8 | 100% ✅ |
| 6. Withdraw | 5/5 | 100% ✅ |
| 7. Interest Rates | 6/6 | 100% ✅ |
| 8. Validators | 11/11 | 100% ✅ |
| 9. Polish | 10/18 | 56% ⏳ |

---

## 🧪 Testing

```bash
# Backend unit tests
cd backend
pytest tests/unit/ -v

# Property-based tests (invariant checking)
pytest tests/property/ -v --hypothesis-show-statistics

# Integration tests (requires running Elements node)
pytest tests/integration/ -v

# Frontend tests
cd frontend
npm test

# Coverage
npm test -- --coverage
```

---

## 🔐 Security

### Formal Verification

All validators undergo formal verification before deployment:

1. **Specification**: Write formal spec defining invariants
2. **Implementation**: Implement validator in SimplicityHL
3. **Proof**: Prove implementation satisfies specification using Coq
4. **Extraction**: Compile to Simplicity bytecode
5. **Audit**: External security audit of code and proofs

### Key Invariants

- **Solvency**: `totalBorrowed ≤ totalLiquidity` (always)
- **Collateralization**: `healthFactor ≥ 1.0` (or liquidatable)
- **Index Monotonicity**: Indices never decrease
- **Conservation**: Asset amounts conserved across transactions

### Security Audits

- [ ] Internal review (in progress)
- [ ] External audit (planned after testnet deployment)
- [ ] Bug bounty program (planned for mainnet)

---

## 🗺️ Roadmap

### Phase 1: MVP ✅ Complete (92%)
- [x] Project constitution and specification
- [x] Implementation plan and architecture design
- [x] Reserve and Debt validators (SimplicityHL) - **1,535 LOC**
- [x] Oracle validator (SimplicityHL) - **330 LOC**
- [x] RAY math library (SimplicityHL) - **235 LOC**
- [x] Formal verification proofs (Coq) - **780 LOC**
- [x] Backend coordinator and API - **Fully functional**
- [x] Frontend UI - **Complete with all features**
- [x] Supply, Withdraw, Borrow, Repay, Liquidate - **All implemented**
- [x] Dynamic interest rates - **AAVE-style model**
- [x] Dashboard with reserve info - **Real-time**
- [x] Transaction history tracking - **Audit trail**
- [x] OpenAPI documentation - **Comprehensive**

### Phase 2: Testnet
- [ ] Deploy to Liquid testnet
- [ ] Integration testing with real testnet transactions
- [ ] Economic simulations and stress testing
- [ ] Community testing program
- [ ] Documentation and tutorials

### Phase 3: Mainnet Preparation
- [ ] External security audit
- [ ] Bug bounty program
- [ ] Governance framework
- [ ] Liquidity mining incentives
- [ ] Mainnet deployment (pending audit approval)

### Future Enhancements
- [ ] Stable rate borrowing
- [ ] Multiple collateral types per position
- [ ] Flash loans
- [ ] Governance token and DAO
- [ ] Confidential transactions support
- [ ] Additional asset support

---

## 💬 Getting Help

### Documentation Resources
- **[Quickstart Guide](QUICKSTART.md)**: Fast track to getting started
- **[Project Status](PROJECT_STATUS_FINAL.md)**: Current implementation status
- **[API Documentation](http://localhost:8000/docs)**: Interactive API reference
- **[Validator Guide](validators/IMPLEMENTATION_GUIDE.md)**: SimplicityHL validator details
- **[Frontend Troubleshooting](frontend/TROUBLESHOOTING.md)**: Common frontend issues

### Common Issues
1. **Backend won't start**: Check Python version (3.11+), run `alembic upgrade head`
2. **Frontend build errors**: Delete `node_modules`, run `npm install` again
3. **Validator compilation**: Requires `simc` compiler from Simplicity repository
4. **Elements node**: Use `./scripts/setup_testnet.sh` for automated setup

### Support
- **Issues**: [GitHub Issues](https://github.com/nitroxgas/SimpleLoan/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/nitroxgas/SimpleLoan/pulls)
- **Development Docs**: See [`development_docs/`](development_docs/) directory

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** the constitution principles (see `.specify/memory/constitution.md`)
4. **Write** tests for all new code
5. **Ensure** all tests pass (`pytest` and `npm test`)
6. **Commit** with conventional commits (`feat:`, `fix:`, `docs:`, etc.)
7. **Push** to your branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Code Standards

- **Python**: Follow PEP 8, use type hints, 100% test coverage for critical paths
- **TypeScript**: Follow Airbnb style guide, strict mode enabled
- **SimplicityHL**: Follow formal verification best practices
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Billau Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🔗 Links

- **Website**: [billau.network](https://billau.network) (coming soon)
- **Documentation**: [docs.billau.network](https://docs.billau.network) (coming soon)
- **Twitter**: [@BillauProtocol](https://twitter.com/BillauProtocol) (coming soon)
- **Discord**: [Join our community](https://discord.gg/billau) (coming soon)
- **Liquid Network**: [liquid.net](https://liquid.net/)
- **Elements Project**: [elementsproject.org](https://elementsproject.org/)
- **Simplicity**: [github.com/BlockstreamResearch/simplicity](https://github.com/BlockstreamResearch/simplicity)

---

## 🙏 Acknowledgments

- **AAVE**: For pioneering the lending pool architecture that inspired this protocol
- **Blockstream**: For developing Liquid Network and Simplicity
- **Elements Project**: For the Elements sidechain platform
- **Bitcoin Community**: For the foundation of trustless, decentralized finance

---

## ⚠️ Disclaimer

**This software is experimental and under active development.**

- **Development Phase**: 92% complete (87/95 tasks)
- **Testnet Ready**: Validators and backend implemented, not yet deployed
- **No Mainnet**: Not audited or approved for mainnet deployment
- **Use at Own Risk**: Educational and testing purposes only
- **No Warranties**: Provided "as is" without any warranties or guarantees

### Current Status
- ✅ **Implementation**: Core protocol complete with formal verification
- ✅ **Validators**: SimplicityHL code written and Coq proofs verified
- ⏳ **Testing**: Integration tests and security audit pending
- ❌ **Deployment**: Not yet deployed to Liquid testnet or mainnet

### Before Production Use
1. ✅ Complete formal verification (DONE)
2. ⏳ Complete integration testing suite
3. ⏳ External security audit
4. ⏳ Bug bounty program
5. ⏳ Testnet deployment and community testing
6. ❌ Mainnet deployment (after audit approval)

---

<div align="center">

**Built with ❤️ by the Billau community**

*Bringing formally verified DeFi to Bitcoin*

[Report Bug](https://github.com/nitroxgas/SimpleLoan/issues) · [Request Feature](https://github.com/nitroxgas/SimpleLoan/issues) · [Documentation](specs/001-utxo-lending-protocol/spec.md)

</div>
