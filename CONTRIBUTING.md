# Contributing to Fantasma Protocol

Thank you for your interest in contributing to Fantasma! This document provides guidelines and instructions for contributing to the project.

## 🌟 Ways to Contribute

- **Code**: Implement features, fix bugs, improve performance
- **Documentation**: Write guides, improve README, add code comments
- **Testing**: Write tests, report bugs, perform security audits
- **Design**: Improve UI/UX, create graphics, design user flows
- **Research**: Formal verification, economic modeling, security analysis
- **Community**: Answer questions, help onboard new contributors

## 📋 Before You Start

1. **Read the Constitution**: Familiarize yourself with [project principles](.specify/memory/constitution.md)
2. **Check Existing Issues**: Look for [open issues](https://github.com/fantasma-protocol/fantasma/issues)
3. **Join Discussions**: Participate in [GitHub Discussions](https://github.com/fantasma-protocol/fantasma/discussions)
4. **Setup Environment**: Follow the [Quickstart Guide](specs/001-utxo-lending-protocol/quickstart.md)

## 🔧 Development Process

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/fantasma.git
cd fantasma
git remote add upstream https://github.com/fantasma-protocol/fantasma.git
```

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Convention**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring
- `perf/` - Performance improvements

### 3. Make Changes

Follow our coding standards:

#### Python (Backend)
```python
# Use type hints
def calculate_health_factor(
    collateral_value: int,
    debt_value: int,
    liquidation_threshold: int
) -> int:
    """
    Calculate health factor for a debt position.
    
    Args:
        collateral_value: Collateral value in RAY
        debt_value: Debt value in RAY
        liquidation_threshold: Threshold in RAY (e.g., 0.8 * RAY)
    
    Returns:
        Health factor in RAY (1.0 * RAY = healthy)
    """
    if debt_value == 0:
        return RAY * 10**9  # Effectively infinite
    
    numerator = ray_mul(collateral_value, liquidation_threshold)
    return ray_div(numerator, debt_value)
```

**Python Standards**:
- Follow PEP 8
- Use type hints for all functions
- Write docstrings (Google style)
- Maximum line length: 100 characters
- Use `black` for formatting
- Use `mypy` for type checking

#### TypeScript (Frontend)
```typescript
// Use explicit types
interface SupplyFormProps {
  onSubmit: (amount: number, asset: string) => Promise<void>;
  disabled?: boolean;
}

export function SupplyForm({ onSubmit, disabled = false }: SupplyFormProps) {
  // Component implementation
}
```

**TypeScript Standards**:
- Enable strict mode
- Use interfaces for object types
- Prefer `const` over `let`
- Use functional components with hooks
- Follow Airbnb style guide

#### SimplicityHL (Validators)
```simplicity
-- Reserve validator with formal specification
validator reserve_validator(old_state: ReserveState, new_state: ReserveState) -> Bool {
  -- Invariant: Solvency must be preserved
  assert(new_state.total_borrowed <= new_state.total_liquidity);
  
  -- Invariant: Indices must be monotonic
  assert(new_state.liquidity_index >= old_state.liquidity_index);
  
  -- Additional checks...
  true
}
```

**SimplicityHL Standards**:
- Write formal specifications first
- Document all invariants
- Prove correctness with Coq
- Keep validators modular and focused

### 4. Write Tests

**Test Requirements**:
- All new features must have tests
- Bug fixes must include regression tests
- Aim for >80% code coverage
- Critical paths require 100% coverage

**Backend Tests**:
```python
# tests/unit/test_ray_math.py
from hypothesis import given, strategies as st

@given(
    a=st.integers(min_value=0, max_value=10**36),
    b=st.integers(min_value=1, max_value=10**36)
)
def test_ray_mul_commutative(a, b):
    """RAY multiplication should be commutative"""
    assert ray_mul(a, b) == ray_mul(b, a)
```

**Frontend Tests**:
```typescript
// tests/components/SupplyForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SupplyForm } from '@/components/SupplyForm';

test('submits form with valid amount', async () => {
  const onSubmit = jest.fn();
  render(<SupplyForm onSubmit={onSubmit} />);
  
  fireEvent.change(screen.getByPlaceholderText('Amount'), {
    target: { value: '1.5' }
  });
  fireEvent.click(screen.getByText('Supply'));
  
  expect(onSubmit).toHaveBeenCalledWith(1.5, 'BTC');
});
```

### 5. Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=src

# Frontend tests
cd frontend
npm test

# Type checking
cd backend && mypy src/
cd frontend && npm run type-check
```

### 6. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

git commit -m "feat(supply): implement aToken minting logic"
git commit -m "fix(oracle): handle stale price feeds correctly"
git commit -m "docs(readme): add installation instructions"
git commit -m "test(borrow): add health factor edge cases"
```

**Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### 7. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## 📝 Pull Request Guidelines

### PR Title
Use conventional commit format:
```
feat(validator): add Reserve UTXO validation logic
```

### PR Description Template
```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Another change

## Testing
How was this tested?

## Constitution Compliance
- [ ] Follows formal verification requirements (if applicable)
- [ ] Liquid Network native (no EVM dependencies)
- [ ] AAVE-inspired architecture maintained
- [ ] Tests included
- [ ] Documentation updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow convention
```

### Review Process

1. **Automated Checks**: CI runs tests, linting, type checking
2. **Code Review**: At least one maintainer reviews
3. **Constitution Check**: Verify compliance with project principles
4. **Security Review**: Critical changes require security review
5. **Approval**: Maintainer approves and merges

## 🔒 Security

### Reporting Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email: security@fantasma.network
2. Include: Detailed description, steps to reproduce, potential impact
3. Wait for response before public disclosure

### Security Best Practices

- Never commit private keys or secrets
- Use environment variables for sensitive data
- Follow principle of least privilege
- Validate all user inputs
- Use parameterized queries (SQL injection prevention)
- Keep dependencies updated

## 🧪 Testing Standards

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies
- Fast execution (<1s per test)

### Integration Tests
- Test component interactions
- Use test database/blockchain
- Slower but more comprehensive

### Property-Based Tests
- Use Hypothesis (Python) for invariant testing
- Test mathematical properties
- Find edge cases automatically

### Formal Verification
- Write Coq proofs for validators
- Prove critical invariants
- Required for all on-chain logic

## 📚 Documentation

### Code Documentation
- **Python**: Google-style docstrings
- **TypeScript**: JSDoc comments
- **SimplicityHL**: Inline comments for complex logic

### User Documentation
- Update README.md for user-facing changes
- Add examples to quickstart guide
- Update API documentation (OpenAPI spec)

### Architecture Documentation
- Document design decisions in `docs/`
- Update data model for schema changes
- Keep architecture diagrams current

## 🎨 Code Style

### Formatting

**Python**:
```bash
# Format with black
black backend/src/

# Sort imports
isort backend/src/

# Lint
flake8 backend/src/
```

**TypeScript**:
```bash
# Format with prettier
npm run format

# Lint
npm run lint
```

### Naming Conventions

**Python**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**TypeScript**:
- Functions/variables: `camelCase`
- Components: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Types/Interfaces: `PascalCase`

**SimplicityHL**:
- Functions: `snake_case`
- Types: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project website (when launched)

Significant contributions may earn:
- Maintainer status
- Governance tokens (future)
- Bug bounty rewards (future)

## 📞 Getting Help

- **Questions**: [GitHub Discussions](https://github.com/fantasma-protocol/fantasma/discussions)
- **Chat**: Discord (coming soon)
- **Email**: dev@fantasma.network

## 📖 Resources

- [Constitution](.specify/memory/constitution.md)
- [Feature Specification](specs/001-utxo-lending-protocol/spec.md)
- [Implementation Plan](specs/001-utxo-lending-protocol/plan.md)
- [Data Model](specs/001-utxo-lending-protocol/data-model.md)
- [API Documentation](specs/001-utxo-lending-protocol/contracts/api.yaml)
- [Quickstart Guide](specs/001-utxo-lending-protocol/quickstart.md)

## 🙏 Thank You

Every contribution, no matter how small, helps make Fantasma better. We appreciate your time and effort!

---

**Questions?** Open a [discussion](https://github.com/fantasma-protocol/fantasma/discussions) or reach out to the maintainers.
