# Fantasma Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Network: Liquid](https://img.shields.io/badge/Network-Liquid-blue.svg)](https://liquid.net/)
[![Language: SimplicityHL](https://img.shields.io/badge/Language-SimplicityHL-green.svg)](https://github.com/BlockstreamResearch/simplicity)
[![Status: Development](https://img.shields.io/badge/Status-Development-orange.svg)]()

> **AAVE-inspired lending protocol with formal verification on Liquid Network**

Fantasma is a decentralized lending protocol that brings AAVE's battle-tested architecture to Bitcoin's Liquid sidechain using formally verified smart contracts. Built with SimplicityHL and adapted for the UTXO model, Fantasma enables users to supply assets, borrow against collateral, and participate in a trustless lending market with mathematical guarantees of correctness.

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

- Python 3.11+
- Node.js 18+
- Elements Core (Liquid node)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/fantasma-protocol/fantasma.git
cd fantasma

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

## 📖 Documentation

- **[Feature Specification](specs/001-utxo-lending-protocol/spec.md)**: Complete feature requirements and user stories
- **[Implementation Plan](specs/001-utxo-lending-protocol/plan.md)**: Technical architecture and design decisions
- **[Data Model](specs/001-utxo-lending-protocol/data-model.md)**: On-chain and off-chain data structures
- **[API Documentation](specs/001-utxo-lending-protocol/contracts/api.yaml)**: OpenAPI specification
- **[Quickstart Guide](specs/001-utxo-lending-protocol/quickstart.md)**: Developer setup instructions
- **[Constitution](.specify/memory/constitution.md)**: Project principles and governance

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

### Phase 1: MVP (Current)
- [x] Project constitution and specification
- [x] Implementation plan and architecture design
- [ ] Reserve and Debt validators (SimplicityHL)
- [ ] Formal verification proofs (Coq)
- [ ] Backend coordinator and API
- [ ] Frontend UI
- [ ] Regtest deployment and testing

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

Copyright (c) 2025 Fantasma Protocol Contributors

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

- **Website**: [fantasma.network](https://fantasma.network) (coming soon)
- **Documentation**: [docs.fantasma.network](https://docs.fantasma.network) (coming soon)
- **Twitter**: [@FantasmaProtocol](https://twitter.com/FantasmaProtocol) (coming soon)
- **Discord**: [Join our community](https://discord.gg/fantasma) (coming soon)
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

- **Testnet Only**: Currently deployed only on Liquid testnet
- **No Mainnet**: Not yet audited or approved for mainnet deployment
- **Use at Own Risk**: Do not use with real funds until formal audit is complete
- **No Warranties**: Provided "as is" without any warranties or guarantees

For production use, wait for:
1. ✅ Complete formal verification
2. ✅ External security audit
3. ✅ Mainnet deployment announcement

---

<div align="center">

**Built with ❤️ by the Fantasma community**

*Bringing formally verified DeFi to Bitcoin*

[Report Bug](https://github.com/fantasma-protocol/fantasma/issues) · [Request Feature](https://github.com/fantasma-protocol/fantasma/issues) · [Documentation](specs/001-utxo-lending-protocol/spec.md)

</div>
