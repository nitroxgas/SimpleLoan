<!--
Sync Impact Report:
Version: 0.0.0 → 1.0.0
Change Type: MAJOR - Initial constitution creation
Modified Principles: N/A (initial creation)
Added Sections: All core principles, security requirements, development workflow, governance
Removed Sections: N/A
Templates Status:
  ✅ spec-template.md - Reviewed, compatible with formal verification requirements
  ✅ plan-template.md - Reviewed, constitution check section ready
  ✅ tasks-template.md - Reviewed, compatible with test-first approach
Follow-up TODOs: None
-->

# Fantasma Constitution

## Core Principles

### I. Formal Verification First (NON-NEGOTIABLE)

All smart contract logic MUST be implemented using SimplicityHL with formal verification proofs before deployment. Every loan validator (Reserve and Debt) MUST have:
- Mathematical proofs of correctness for core invariants
- Formal specification of state transitions
- Verified bounds on collateralization ratios
- Proven safety properties (no fund loss, no unauthorized access)

**Rationale**: Financial protocols handling real assets require mathematical certainty, not just testing. Formal verification prevents entire classes of vulnerabilities that have cost billions in DeFi exploits.

### II. Liquid Network Native

All implementations MUST be designed for the Liquid Network (initially testnet) with future compatibility for Elements sidechains:
- Use Liquid-specific features (confidential transactions, issued assets)
- Leverage Bitcoin's security model through Liquid's federation
- Design for eventual Elements sidechain portability
- MUST NOT depend on Ethereum-specific constructs (e.g., Solidity patterns)

**Rationale**: Liquid provides Bitcoin-grade security with enhanced privacy and asset issuance capabilities essential for institutional DeFi. Elements compatibility ensures future extensibility.

### III. AAVE-Inspired Architecture

Loan validator design MUST follow AAVE's proven lending pool architecture adapted for SimplicityHL:
- **Reserve Validators**: Manage liquidity pools, interest rates, and collateral factors
- **Debt Validators**: Track borrowing positions, health factors, and liquidation thresholds
- Clear separation between reserve management and debt tracking
- Support for multiple collateral types and borrowed assets

**Rationale**: AAVE's architecture has been battle-tested with billions in TVL. Adapting proven patterns reduces design risk while innovating on the verification layer.

### IV. Testnet-First Development

All development MUST occur on Liquid testnet with comprehensive testing before any mainnet consideration:
- Complete feature implementation and testing on testnet
- Formal verification proofs validated on testnet deployments
- Economic simulations and stress testing on testnet
- Security audits completed before mainnet deployment consideration

**Rationale**: Financial protocols require extensive validation. Testnet-first development prevents costly mainnet mistakes and enables rapid iteration.

### V. Modular Validator Design

Each validator (Reserve, Debt) MUST be independently verifiable and composable:
- Self-contained formal specifications
- Clear interface boundaries between validators
- Independent deployment and upgrade paths
- Minimal cross-validator dependencies

**Rationale**: Modularity enables independent verification, easier auditing, and safer upgrades. Each component can be proven correct in isolation before composition.

### VI. Observability and Transparency

All validator state transitions MUST be observable and auditable:
- Comprehensive event logging for all state changes
- Public queryable state for reserves and debt positions
- Clear audit trails for liquidations and interest accrual
- Monitoring hooks for health factor tracking

**Rationale**: DeFi protocols require transparency for user trust and protocol security. Observable state enables off-chain monitoring and early risk detection.

## Security Requirements

### Cryptographic Standards

- MUST use Liquid Network's native cryptographic primitives
- Confidential transactions MUST be used for privacy-sensitive operations
- All signatures MUST follow Bitcoin/Liquid standards (Schnorr/ECDSA)
- Random number generation MUST use verifiable randomness sources

### Access Control

- Multi-signature governance for protocol parameter updates
- Time-locked administrative functions (minimum 24-hour delay)
- Emergency pause mechanisms with clear activation criteria
- Role-based access control for different validator operations

### Economic Security

- Collateralization ratios MUST be formally verified to prevent undercollateralization
- Liquidation mechanisms MUST be proven to maintain protocol solvency
- Interest rate models MUST be bounded and formally specified
- Oracle dependencies MUST have fallback mechanisms and staleness checks

## Development Workflow

### Implementation Phases

1. **Formal Specification**: Write SimplicityHL specifications with formal properties
2. **Proof Development**: Develop and verify mathematical proofs of correctness
3. **Implementation**: Implement validators matching formal specifications
4. **Testnet Deployment**: Deploy to Liquid testnet for integration testing
5. **Security Audit**: External audit of both code and formal proofs
6. **Mainnet Consideration**: Only after complete testnet validation

### Code Review Requirements

- All SimplicityHL code MUST be reviewed by at least two developers
- Formal proofs MUST be reviewed by verification specialists
- Economic parameters MUST be reviewed by protocol economists
- Security-critical changes require additional security review

### Testing Standards

- Unit tests for all validator functions
- Integration tests for cross-validator interactions
- Property-based tests matching formal specifications
- Economic simulation tests for various market conditions
- Testnet stress testing before mainnet consideration

## Governance

This constitution supersedes all other development practices. All protocol development, validator implementations, and deployment decisions MUST comply with these principles.

### Amendment Process

- Constitution amendments require documented rationale and impact analysis
- Major changes (new principles, removed requirements) require community review
- Minor changes (clarifications, updates) can be fast-tracked with team consensus
- All amendments MUST update version number following semantic versioning

### Compliance Verification

- All pull requests MUST include constitution compliance checklist
- Formal verification proofs MUST be included for smart contract changes
- Security requirements MUST be verified before merge
- Complexity additions MUST be justified against simplicity principles

### Version Control

- MAJOR: Breaking changes to core principles or security requirements
- MINOR: New principles added or significant expansions
- PATCH: Clarifications, typo fixes, non-semantic updates

**Version**: 1.0.0 | **Ratified**: 2025-11-06 | **Last Amended**: 2025-11-06
