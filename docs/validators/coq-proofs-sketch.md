# Coq Proof Sketches for Fantasma Protocol

**Purpose**: Formal verification of core protocol invariants  
**Tool**: Coq Proof Assistant (v8.17+)  
**Status**: Specification only - awaiting implementation

## Overview

Three critical invariants must be proven mathematically to ensure protocol safety:

1. **Solvency**: Total borrowed never exceeds total liquidity
2. **Index Monotonicity**: Interest indices never decrease
3. **Health Factor**: Liquidation logic preserves collateralization

## Proof 1: Solvency Invariant

### Statement

```coq
(* solvency.v *)

Require Import Coq.ZArith.ZArith.
Require Import Coq.Lists.List.

Open Scope Z_scope.

(* Reserve state definition *)
Record Reserve := {
  asset_id : Z;
  total_liquidity : Z;
  total_borrowed : Z;
  liquidity_index : Z;
  borrow_index : Z;
}.

(* Solvency invariant *)
Definition solvency (r : Reserve) : Prop :=
  r.(total_borrowed) <= r.(total_liquidity).

(* Well-formed reserve *)
Definition well_formed_reserve (r : Reserve) : Prop :=
  r.(total_liquidity) >= 0 /\
  r.(total_borrowed) >= 0 /\
  r.(liquidity_index) > 0 /\
  r.(borrow_index) > 0.
```

### Theorem: Solvency Preserved Across Operations

```coq
(* Supply operation preserves solvency *)
Theorem supply_preserves_solvency:
  forall (r : Reserve) (amount : Z),
    well_formed_reserve r ->
    solvency r ->
    amount > 0 ->
    let r' := {| 
      asset_id := r.(asset_id);
      total_liquidity := r.(total_liquidity) + amount;
      total_borrowed := r.(total_borrowed);
      liquidity_index := r.(liquidity_index);
      borrow_index := r.(borrow_index)
    |} in
    solvency r'.

Proof.
  intros r amount Hwf Hsolv Hamount.
  unfold solvency in *.
  simpl.
  (* total_borrowed stays same, total_liquidity increases *)
  omega.
Qed.

(* Withdraw operation preserves solvency when valid *)
Theorem withdraw_preserves_solvency:
  forall (r : Reserve) (amount : Z),
    well_formed_reserve r ->
    solvency r ->
    amount > 0 ->
    r.(total_liquidity) - amount >= r.(total_borrowed) ->
    let r' := {| 
      asset_id := r.(asset_id);
      total_liquidity := r.(total_liquidity) - amount;
      total_borrowed := r.(total_borrowed);
      liquidity_index := r.(liquidity_index);
      borrow_index := r.(borrow_index)
    |} in
    solvency r'.

Proof.
  intros r amount Hwf Hsolv Hamount Hvalid.
  unfold solvency in *.
  simpl.
  (* By assumption: total_liquidity - amount >= total_borrowed *)
  omega.
Qed.

(* Borrow operation maintains solvency *)
Theorem borrow_maintains_solvency:
  forall (r : Reserve) (amount : Z),
    well_formed_reserve r ->
    solvency r ->
    amount > 0 ->
    amount <= r.(total_liquidity) - r.(total_borrowed) ->
    let r' := {| 
      asset_id := r.(asset_id);
      total_liquidity := r.(total_liquidity) - amount;
      total_borrowed := r.(total_borrowed) + amount;
      liquidity_index := r.(liquidity_index);
      borrow_index := r.(borrow_index)
    |} in
    solvency r'.

Proof.
  intros r amount Hwf Hsolv Hamount Havail.
  unfold solvency in *.
  simpl.
  (* total_borrowed' = total_borrowed + amount *)
  (* total_liquidity' = total_liquidity - amount *)
  (* Need to show: total_borrowed + amount <= total_liquidity - amount *)
  (* Equivalently: total_borrowed + 2*amount <= total_liquidity *)
  omega.
Qed.

(* Main solvency theorem *)
Theorem solvency_invariant:
  forall (r : Reserve) (op : Operation),
    well_formed_reserve r ->
    solvency r ->
    valid_operation r op ->
    solvency (apply_operation r op).

Proof.
  intros r op Hwf Hsolv Hvalid.
  destruct op as [Supply a | Withdraw a | Borrow a | Repay a].
  - (* Supply case *)
    apply supply_preserves_solvency; assumption.
  - (* Withdraw case *)
    apply withdraw_preserves_solvency; assumption.
  - (* Borrow case *)
    apply borrow_maintains_solvency; assumption.
  - (* Repay case *)
    (* Similar to supply: total_borrowed decreases, total_liquidity increases *)
    admit.
Admitted.
```

## Proof 2: Index Monotonicity

### Statement

```coq
(* index_accrual.v *)

Require Import Coq.ZArith.ZArith.
Require Import Coq.Reals.Reals.

Open Scope Z_scope.

(* RAY constant: 10^27 *)
Definition RAY : Z := 1000000000000000000000000000.

(* RAY multiplication with rounding *)
Definition ray_mul (a b : Z) : Z :=
  (a * b + RAY / 2) / RAY.

(* Index accrual function *)
Definition accrue_index (index rate time_delta : Z) : Z :=
  let rate_per_period := ray_mul (rate * RAY) (time_delta * RAY) / RAY in
  let accrued := ray_mul index rate_per_period in
  index + accrued.
```

### Theorem: Indices Never Decrease

```coq
(* Monotonicity lemma *)
Lemma accrue_index_monotonic:
  forall (index rate time_delta : Z),
    index > 0 ->
    rate >= 0 ->
    time_delta >= 0 ->
    accrue_index index rate time_delta >= index.

Proof.
  intros index rate td Hindex Hrate Htime.
  unfold accrue_index.
  (* Show that accrued >= 0 *)
  assert (Haccrued: ray_mul index (ray_mul (rate * RAY) (td * RAY) / RAY) >= 0).
  {
    (* rate >= 0 and td >= 0 implies product >= 0 *)
    (* ray_mul preserves non-negativity *)
    admit.
  }
  (* Therefore index + accrued >= index *)
  omega.
Admitted.

(* Liquidity index never decreases *)
Theorem liquidity_index_monotonic:
  forall (r1 r2 : Reserve) (t1 t2 : Z),
    well_formed_reserve r1 ->
    well_formed_reserve r2 ->
    t1 <= t2 ->
    r2 = update_indices r1 (t2 - t1) ->
    r2.(liquidity_index) >= r1.(liquidity_index).

Proof.
  intros r1 r2 t1 t2 Hwf1 Hwf2 Htime Hupdate.
  unfold update_indices in Hupdate.
  (* Apply accrue_index_monotonic *)
  apply accrue_index_monotonic.
  - (* liquidity_index > 0 *)
    destruct Hwf1 as [_ [_ [Hli _]]]. assumption.
  - (* rate >= 0 *)
    (* Interest rates are always non-negative *)
    admit.
  - (* time_delta >= 0 *)
    omega.
Admitted.

(* Borrow index never decreases *)
Theorem borrow_index_monotonic:
  forall (r1 r2 : Reserve) (t1 t2 : Z),
    well_formed_reserve r1 ->
    well_formed_reserve r2 ->
    t1 <= t2 ->
    r2 = update_indices r1 (t2 - t1) ->
    r2.(borrow_index) >= r1.(borrow_index).

Proof.
  (* Similar to liquidity_index_monotonic *)
  admit.
Admitted.
```

## Proof 3: Health Factor Preservation

### Statement

```coq
(* health_factor.v *)

Require Import Coq.ZArith.ZArith.
Require Import Coq.QArith.QArith.

Open Scope Z_scope.

(* Debt position definition *)
Record DebtPosition := {
  user_address : Z;
  position_id : Z;
  principal : Z;
  borrow_index_at_open : Z;
  collateral_amount : Z;
  collateral_asset_id : Z;
  borrowed_asset_id : Z;
}.

(* Oracle price function *)
Parameter get_price : Z -> Z -> Z.

(* Health factor calculation *)
Definition health_factor (pos : DebtPosition) (current_borrow_index : Z) 
                         (liquidation_threshold : Z) : Z :=
  let current_debt := ray_mul (pos.(principal) * RAY) 
                              (ray_div current_borrow_index pos.(borrow_index_at_open)) / RAY in
  let collateral_value := get_price pos.(collateral_asset_id) pos.(collateral_amount) in
  let debt_value := get_price pos.(borrowed_asset_id) current_debt in
  let weighted_collateral := ray_mul collateral_value liquidation_threshold in
  ray_div weighted_collateral debt_value.

(* Liquidatable condition *)
Definition liquidatable (pos : DebtPosition) (current_borrow_index : Z) 
                        (liquidation_threshold : Z) : Prop :=
  health_factor pos current_borrow_index liquidation_threshold < RAY.
```

### Theorem: Liquidation Improves Health Factor

```coq
(* Liquidation reduces debt and collateral proportionally *)
Theorem liquidation_improves_health:
  forall (pos : DebtPosition) (current_index threshold : Z) (liquidation_amount : Z),
    liquidatable pos current_index threshold ->
    liquidation_amount > 0 ->
    let current_debt := ray_mul (pos.(principal) * RAY) 
                                (ray_div current_index pos.(borrow_index_at_open)) / RAY in
    liquidation_amount <= current_debt ->
    let collateral_seized := (pos.(collateral_amount) * liquidation_amount) / current_debt +
                             ((pos.(collateral_amount) * liquidation_amount) / current_debt * LIQUIDATION_BONUS) / RAY in
    let pos' := {|
      user_address := pos.(user_address);
      position_id := pos.(position_id);
      principal := current_debt - liquidation_amount;
      borrow_index_at_open := current_index;
      collateral_amount := pos.(collateral_amount) - collateral_seized;
      collateral_asset_id := pos.(collateral_asset_id);
      borrowed_asset_id := pos.(borrowed_asset_id)
    |} in
    health_factor pos' current_index threshold >= health_factor pos current_index threshold.

Proof.
  intros pos current_index threshold liq_amt Hliq Hamt Hvalid collateral_seized pos'.
  unfold health_factor.
  (* Show that reducing debt and collateral proportionally (with bonus) *)
  (* maintains or improves the health factor *)
  (* Key insight: liquidation_bonus ensures HF improves *)
  admit.
Admitted.

(* Healthy positions cannot be liquidated *)
Theorem healthy_not_liquidatable:
  forall (pos : DebtPosition) (current_index threshold : Z),
    health_factor pos current_index threshold >= RAY ->
    ~ liquidatable pos current_index threshold.

Proof.
  intros pos current_index threshold Hhealthy.
  unfold liquidatable.
  omega.
Qed.

(* LTV constraint ensures initial health *)
Theorem ltv_ensures_health:
  forall (pos : DebtPosition) (ltv liquidation_threshold : Z),
    ltv <= liquidation_threshold ->
    let collateral_value := get_price pos.(collateral_asset_id) pos.(collateral_amount) in
    let debt_value := get_price pos.(borrowed_asset_id) pos.(principal) in
    debt_value <= ray_mul collateral_value ltv ->
    health_factor pos pos.(borrow_index_at_open) liquidation_threshold >= RAY.

Proof.
  intros pos ltv threshold Hltv_le collateral_value debt_value Hltv_check.
  unfold health_factor.
  (* Show that if debt <= collateral * ltv and ltv <= threshold *)
  (* then health_factor = (collateral * threshold) / debt >= RAY *)
  admit.
Admitted.
```

## Proof Structure

```
Protocol Correctness
├── Solvency (solvency.v)
│   ├── supply_preserves_solvency
│   ├── withdraw_preserves_solvency
│   ├── borrow_maintains_solvency
│   └── repay_preserves_solvency
├── Index Monotonicity (index_accrual.v)
│   ├── accrue_index_monotonic
│   ├── liquidity_index_monotonic
│   └── borrow_index_monotonic
└── Health Factor (health_factor.v)
    ├── liquidation_improves_health
    ├── healthy_not_liquidatable
    └── ltv_ensures_health
```

## Dependencies

```coq
(* Common.v - Shared definitions *)
Require Import Coq.ZArith.ZArith.
Require Import Coq.QArith.QArith.
Require Import Coq.Lists.List.

(* RAY math library *)
Require Import RayMath.

(* Protocol state definitions *)
Require Import ReserveState.
Require Import DebtPosition.
```

## Compilation Instructions

```bash
# Install Coq
opam install coq

# Compile proofs
cd validators/reserve/proofs
coqc Common.v
coqc RayMath.v
coqc ReserveState.v
coqc solvency.v
coqc index_accrual.v

cd ../../debt/proofs
coqc DebtPosition.v
coqc health_factor.v

# Verify all proofs
coqc -R . Fantasma solvency.v
coqc -R . Fantasma index_accrual.v
coqc -R . Fantasma health_factor.v
```

## Testing with Coq

```coq
(* Example test case *)
Example test_solvency_supply:
  let r := {|
    asset_id := 0;
    total_liquidity := 1000000;
    total_borrowed := 500000;
    liquidity_index := RAY;
    borrow_index := RAY
  |} in
  let r' := apply_operation r (Supply 100000) in
  solvency r' = true.

Proof.
  reflexivity.
Qed.
```

## References

- [Coq Tutorial](https://coq.inria.fr/tutorial)
- [Software Foundations](https://softwarefoundations.cis.upenn.edu/)
- [Formal Verification of Smart Contracts](https://github.com/ethereum/wiki/wiki/Formal-verification-of-smart-contracts)
- [AAVE Security Audits](https://docs.aave.com/developers/security-and-audits)

## Next Steps

1. Complete proof implementations
2. Add comprehensive test cases
3. Verify with Coq proof checker
4. Generate proof certificates
5. Integrate with SimplicityHL validators
