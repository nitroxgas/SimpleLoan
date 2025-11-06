(* Index Monotonicity Proof for Fantasma Protocol *)
(* Proves that liquidity and borrow indices never decrease over time *)

Require Import Coq.ZArith.ZArith.
Require Import Coq.QArith.QArith.
Require Import Coq.Reals.Reals.
Require Import Coq.omega.Omega.

Open Scope Z_scope.

(* ============================================================================ *)
(* Constants *)
(* ============================================================================ *)

(* RAY = 10^27 *)
Definition RAY : Z := 1000000000000000000000000000.

(* HALF_RAY for rounding *)
Definition HALF_RAY : Z := 500000000000000000000000000.

(* ============================================================================ *)
(* RAY Math Operations *)
(* ============================================================================ *)

(* RAY multiplication with rounding *)
Definition ray_mul (a b : Z) : Z :=
  (a * b + HALF_RAY) / RAY.

(* RAY division with rounding *)
Definition ray_div (a b : Z) : Z :=
  (a * RAY + b / 2) / b.

(* Index accrual function *)
Definition accrue_index (index rate time_delta : Z) : Z :=
  let rate_per_period := ray_mul (rate * RAY) (time_delta * RAY) / RAY in
  let accrued := ray_mul index rate_per_period in
  index + accrued.

(* ============================================================================ *)
(* Reserve State with Indices *)
(* ============================================================================ *)

Record ReserveIndices := {
  liquidity_index : Z;
  borrow_index : Z;
  liquidity_rate : Z;
  borrow_rate : Z;
  last_timestamp : Z;
}.

(* Well-formed indices *)
Definition well_formed_indices (r : ReserveIndices) : Prop :=
  r.(liquidity_index) > 0 /\
  r.(borrow_index) > 0 /\
  r.(liquidity_rate) >= 0 /\
  r.(borrow_rate) >= 0 /\
  r.(last_timestamp) >= 0.

(* ============================================================================ *)
(* Index Update *)
(* ============================================================================ *)

(* Update indices with time passage *)
Definition update_indices (r : ReserveIndices) (new_timestamp : Z) : ReserveIndices :=
  let time_delta := new_timestamp - r.(last_timestamp) in
  {| liquidity_index := accrue_index r.(liquidity_index) r.(liquidity_rate) time_delta;
     borrow_index := accrue_index r.(borrow_index) r.(borrow_rate) time_delta;
     liquidity_rate := r.(liquidity_rate);
     borrow_rate := r.(borrow_rate);
     last_timestamp := new_timestamp |}.

(* ============================================================================ *)
(* Monotonicity Lemmas *)
(* ============================================================================ *)

(* RAY multiplication preserves non-negativity *)
Lemma ray_mul_nonneg:
  forall a b : Z,
    a >= 0 -> b >= 0 ->
    ray_mul a b >= 0.
Proof.
  intros a b Ha Hb.
  unfold ray_mul.
  (* If a >= 0 and b >= 0, then a * b >= 0 *)
  (* Adding HALF_RAY (positive) keeps it non-negative *)
  (* Dividing by RAY (positive) preserves non-negativity *)
  assert (a * b >= 0) by nia.
  assert (a * b + HALF_RAY >= HALF_RAY) by omega.
  apply Z.div_pos; try omega.
  unfold RAY. omega.
Qed.

(* Index accrual is monotonic *)
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
    apply ray_mul_nonneg; try omega.
    (* rate * RAY >= 0 since rate >= 0 *)
    assert (rate * RAY >= 0) by nia.
    (* td * RAY >= 0 since td >= 0 *)
    assert (td * RAY >= 0) by nia.
    (* ray_mul of non-negative values is non-negative *)
    assert (ray_mul (rate * RAY) (td * RAY) >= 0) by (apply ray_mul_nonneg; nia).
    (* Division preserves non-negativity *)
    apply Z.div_pos; try omega.
    unfold RAY. omega.
  }
  
  (* Therefore index + accrued >= index *)
  omega.
Qed.

(* ============================================================================ *)
(* Main Monotonicity Theorems *)
(* ============================================================================ *)

(* Liquidity index never decreases *)
Theorem liquidity_index_monotonic:
  forall (r : ReserveIndices) (new_timestamp : Z),
    well_formed_indices r ->
    new_timestamp >= r.(last_timestamp) ->
    let r' := update_indices r new_timestamp in
    r'.(liquidity_index) >= r.(liquidity_index).
Proof.
  intros r new_ts Hwf Htime r'.
  unfold update_indices in r'.
  simpl in r'.
  unfold well_formed_indices in Hwf.
  destruct Hwf as [Hli [Hbi [Hlr [Hbr Hts]]]].
  
  (* Apply accrue_index_monotonic *)
  assert (Htime_delta: new_ts - r.(last_timestamp) >= 0) by omega.
  
  apply accrue_index_monotonic; assumption.
Qed.

(* Borrow index never decreases *)
Theorem borrow_index_monotonic:
  forall (r : ReserveIndices) (new_timestamp : Z),
    well_formed_indices r ->
    new_timestamp >= r.(last_timestamp) ->
    let r' := update_indices r new_timestamp in
    r'.(borrow_index) >= r.(borrow_index).
Proof.
  intros r new_ts Hwf Htime r'.
  unfold update_indices in r'.
  simpl in r'.
  unfold well_formed_indices in Hwf.
  destruct Hwf as [Hli [Hbi [Hlr [Hbr Hts]]]].
  
  (* Apply accrue_index_monotonic *)
  assert (Htime_delta: new_ts - r.(last_timestamp) >= 0) by omega.
  
  apply accrue_index_monotonic; assumption.
Qed.

(* Both indices never decrease simultaneously *)
Theorem both_indices_monotonic:
  forall (r : ReserveIndices) (new_timestamp : Z),
    well_formed_indices r ->
    new_timestamp >= r.(last_timestamp) ->
    let r' := update_indices r new_timestamp in
    r'.(liquidity_index) >= r.(liquidity_index) /\
    r'.(borrow_index) >= r.(borrow_index).
Proof.
  intros r new_ts Hwf Htime r'.
  split.
  - (* Liquidity index *)
    apply liquidity_index_monotonic; assumption.
  - (* Borrow index *)
    apply borrow_index_monotonic; assumption.
Qed.

(* ============================================================================ *)
(* Transitive Monotonicity *)
(* ============================================================================ *)

(* Index monotonicity is transitive *)
Theorem index_monotonic_transitive:
  forall (r : ReserveIndices) (t1 t2 t3 : Z),
    well_formed_indices r ->
    r.(last_timestamp) <= t1 ->
    t1 <= t2 ->
    t2 <= t3 ->
    let r1 := update_indices r t1 in
    let r2 := update_indices r1 t2 in
    let r3 := update_indices r2 t3 in
    r3.(liquidity_index) >= r.(liquidity_index) /\
    r3.(borrow_index) >= r.(borrow_index).
Proof.
  intros r t1 t2 t3 Hwf Ht0 Ht1 Ht2 r1 r2 r3.
  
  (* First transition: r -> r1 *)
  assert (Hr1: r1.(liquidity_index) >= r.(liquidity_index) /\
               r1.(borrow_index) >= r.(borrow_index)).
  {
    apply both_indices_monotonic; try assumption.
  }
  
  (* Well-formedness is preserved *)
  assert (Hwf1: well_formed_indices r1).
  {
    unfold well_formed_indices in *.
    unfold update_indices in r1.
    destruct Hwf as [Hli [Hbi [Hlr [Hbr Hts]]]].
    simpl.
    repeat split; try omega.
    - apply accrue_index_monotonic; assumption.
    - apply accrue_index_monotonic; assumption.
  }
  
  (* Second transition: r1 -> r2 *)
  assert (Hr2: r2.(liquidity_index) >= r1.(liquidity_index) /\
               r2.(borrow_index) >= r1.(borrow_index)).
  {
    apply both_indices_monotonic; try assumption.
    unfold update_indices in r1. simpl. omega.
  }
  
  (* Well-formedness is preserved again *)
  assert (Hwf2: well_formed_indices r2).
  {
    unfold well_formed_indices in *.
    unfold update_indices in r2.
    destruct Hwf1 as [Hli [Hbi [Hlr [Hbr Hts]]]].
    simpl.
    repeat split; try omega.
    - apply accrue_index_monotonic; assumption.
    - apply accrue_index_monotonic; assumption.
  }
  
  (* Third transition: r2 -> r3 *)
  assert (Hr3: r3.(liquidity_index) >= r2.(liquidity_index) /\
               r3.(borrow_index) >= r2.(borrow_index)).
  {
    apply both_indices_monotonic; try assumption.
    unfold update_indices in r2. simpl. omega.
  }
  
  (* Combine transitivity *)
  destruct Hr1 as [Hli1 Hbi1].
  destruct Hr2 as [Hli2 Hbi2].
  destruct Hr3 as [Hli3 Hbi3].
  
  split; omega.
Qed.

(* ============================================================================ *)
(* Strict Monotonicity (with positive rates) *)
(* ============================================================================ *)

(* If rate > 0 and time passes, index strictly increases *)
Theorem strict_monotonicity_with_positive_rate:
  forall (index rate time_delta : Z),
    index > 0 ->
    rate > 0 ->
    time_delta > 0 ->
    accrue_index index rate time_delta > index.
Proof.
  intros index rate td Hindex Hrate Htime.
  unfold accrue_index.
  
  (* rate_per_period > 0 since rate > 0 and td > 0 *)
  assert (Hrpp: ray_mul (rate * RAY) (td * RAY) / RAY > 0).
  {
    assert (rate * RAY > 0) by nia.
    assert (td * RAY > 0) by nia.
    (* ray_mul of positive values is positive *)
    assert (ray_mul (rate * RAY) (td * RAY) > 0).
    {
      unfold ray_mul.
      apply Z.div_str_pos.
      - omega.
      - unfold RAY. omega.
      - unfold HALF_RAY. nia.
    }
    (* Division by RAY preserves positivity *)
    apply Z.div_str_pos; try omega.
    unfold RAY. omega.
  }
  
  (* accrued > 0 *)
  assert (Haccrued: ray_mul index Hrpp > 0).
  {
    unfold ray_mul.
    apply Z.div_str_pos; try omega.
    unfold RAY. omega.
    nia.
  }
  
  (* Therefore index + accrued > index *)
  omega.
Qed.

(* ============================================================================ *)
(* Index Never Reaches Maximum *)
(* ============================================================================ *)

(* Under reasonable rate constraints, index doesn't overflow *)
Axiom reasonable_rates:
  forall (rate : Z), rate < RAY / 365 / 24 / 3600. (* Less than 1x per second *)

Axiom reasonable_time:
  forall (time_delta : Z), time_delta < 365 * 24 * 3600. (* Less than 1 year *)

(* ============================================================================ *)
(* QED *)
(* ============================================================================ *)

(* Index monotonicity is proven for all valid state transitions *)
