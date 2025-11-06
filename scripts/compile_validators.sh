#!/bin/bash
# Compile SimplicityHL Validators to Simplicity Bytecode
# Requires: simc (SimplicityHL compiler)

set -e  # Exit on error

echo "========================================"
echo "Fantasma Protocol Validator Compilation"
echo "========================================"
echo ""

# Check for simc compiler
if ! command -v simc &> /dev/null; then
    echo "Error: simc compiler not found"
    echo "Install with: cargo install --features=serde simplicityhl"
    exit 1
fi

# Create output directory
mkdir -p validators/compiled

echo "Compiling RAY Math Library..."
simc compile validators/lib/ray_math.simf -o validators/compiled/ray_math.simp
echo "✓ RAY math library compiled"
echo ""

echo "Compiling Reserve Validator..."
simc compile validators/reserve/reserve.simf -o validators/compiled/reserve.simp
echo "✓ Reserve validator compiled"
echo ""

echo "Compiling Debt Validator..."
simc compile validators/debt/debt.simf -o validators/compiled/debt.simp
echo "✓ Debt validator compiled"
echo ""

echo "Compiling Oracle Validator..."
simc compile validators/oracle/oracle_validator.simf -o validators/compiled/oracle.simp
echo "✓ Oracle validator compiled"
echo ""

echo "========================================"
echo "All validators compiled successfully!"
echo "========================================"
echo ""
echo "Compiled files:"
ls -lh validators/compiled/
echo ""

# Generate validator info
echo "Generating validator information..."
echo ""

if command -v hal-simplicity &> /dev/null; then
    echo "Reserve Validator Info:"
    hal-simplicity simplicity info < validators/compiled/reserve.simp
    echo ""
    
    echo "Debt Validator Info:"
    hal-simplicity simplicity info < validators/compiled/debt.simp
    echo ""
    
    echo "Oracle Validator Info:"
    hal-simplicity simplicity info < validators/compiled/oracle.simp
    echo ""
else
    echo "Note: Install hal-simplicity to view validator addresses"
    echo "  git clone https://github.com/BlockstreamResearch/hal-simplicity"
    echo "  cd hal-simplicity && cargo install --path ."
fi

echo "Next steps:"
echo "1. Verify Coq proofs: ./scripts/verify_proofs.sh"
echo "2. Test on Liquid testnet: ./scripts/test_validators_regtest.sh"
echo "3. Deploy to testnet: ./scripts/deploy_validators.sh"
