# Fantasma Validators Quick Start

**5-Minute Guide to Compile & Deploy**

## Prerequisites

```bash
# 1. Install SimplicityHL compiler
cargo install --features=serde simplicityhl

# 2. Install hal-simplicity
git clone https://github.com/BlockstreamResearch/hal-simplicity
cd hal-simplicity && cargo install --path .

# 3. Install Coq (for proof verification)
opam install coq

# 4. (Optional) Install Elements Core for testnet
# Download from: https://elementsproject.org/
```

## Quick Commands

### Compile All Validators
```bash
cd fantasma
./scripts/compile_validators.sh
```

**Output**: `validators/compiled/*.simp` files

### Verify All Proofs
```bash
./scripts/verify_proofs.sh
```

**Output**: `validators/**/proofs/*.vo` files + verification report

### Deploy to Testnet
```bash
# Start Elements node
elementsd -chain=liquidtestnet -daemon

# Deploy validators
./scripts/deploy_validators.sh
```

**Output**: `validators/deployed_validators.csv` + `validators/DEPLOYMENT.md`

## File Locations

### SimplicityHL Code
- `validators/lib/ray_math.simf` - Math library
- `validators/reserve/reserve.simf` - Reserve validator
- `validators/debt/debt.simf` - Debt validator
- `validators/oracle/oracle_validator.simf` - Oracle validator

### Coq Proofs
- `validators/reserve/proofs/solvency.v` - Solvency proof
- `validators/reserve/proofs/index_accrual.v` - Monotonicity proof
- `validators/debt/proofs/health_factor.v` - Health factor proof

### Documentation
- `validators/IMPLEMENTATION_GUIDE.md` - Full guide
- `validators/README.md` - Architecture overview
- `T070-T080_SUMMARY.md` - Implementation summary

## Testing Individual Validators

```bash
# Test RAY math
simc test validators/lib/ray_math.simf

# Test reserve validator
simc test validators/reserve/reserve.simf

# Test debt validator
simc test validators/debt/debt.simf
```

## Get Validator Addresses

```bash
# Reserve validator address
hal-simplicity simplicity info < validators/compiled/reserve.simp

# Debt validator address
hal-simplicity simplicity info < validators/compiled/debt.simp

# Oracle validator address
hal-simplicity simplicity info < validators/compiled/oracle.simp
```

## Testnet Resources

- **Faucet**: https://liquidtestnet.com/faucet
- **Explorer**: https://blockstream.info/liquidtestnet/
- **RPC**: liquidtestnet.com:7041

## Common Issues

### "simc: command not found"
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

### "coqc: command not found"
```bash
eval $(opam env)
```

### "Cannot connect to Elements node"
```bash
elements-cli -chain=liquidtestnet getblockchaininfo
```

## Next Steps

1. ✅ Compile validators
2. ✅ Verify proofs
3. ✅ Deploy to testnet
4. ✅ Test transactions
5. ✅ Monitor execution
6. ✅ Security audit
7. ✅ Mainnet deployment

## Support

- Implementation Guide: `validators/IMPLEMENTATION_GUIDE.md`
- Task Summary: `T070-T080_SUMMARY.md`
- Phase 8 Summary: `PHASE_8_COMPLETE.md`

---

**Ready to compile? Run**: `./scripts/compile_validators.sh`
