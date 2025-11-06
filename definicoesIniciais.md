Plano técnico completo e utilizável para implementar um sistema de lending inspirado na AAVE, adaptado às diferenças fundamentais do modelo UTXO/SimplicityHL. Vou cobrir:

* Diferenças arquiteturais EVM vs UTXO (implicações).

* Mapeamento dos principais componentes da AAVE para construções SimplicityHL.

* Modelagem de dados e tokens (collateral, aTokens, debt positions).

* Matemática de juros e índice acumulado (com passos numéricos).

* Operações principais: deposit, withdraw, borrow, repay, liquidate — com lógica e fluxos UTXO.

* Estratégia de oráculos e atualização de preço.

* Segurança, limites práticos e otimizações (tamanho de UTXO, fees, atomicidade).

* Estrutura de testes e ferramentas / simulações que você deve rodar.

* Um esboço em pseudo-SimplicityHL (blocos lógicos e contratos de estado) — pronto para tradução para código SimplicityHL real.

Vou assumir algumas decisões por pragmatismo (sem te fazer perguntas) — se quiser alterar alguma depois, ajustamos:

**Assunções principais**

1. Rede alvo: Liquid (sidechain com SimplicityHL disponível) — UTXO-based, scripts em SimplicityHL.

2. Existirão tokens representando ativos (pe. tokenized BTC, USDT) compatíveis com Liquid (confiaremos que já há peg-ins/asset issuance).

3. Não vamos implementar todas features AAVE (ex.: governance, incentives complexos) — foco em core lending: depósito (supply), retirada, empréstimo, reembolso, liquidação.

4. Oráculo de preço (externo) fornece preço por pair off-chain \+ assinatura on-chain (ou oracle-UTXO) e será confiável e com alta disponibilidade.

5. Usuários interagirão via transações UTXO assinadas por eles; algumas operações podem requerer um *coordinator* off-chain para juntar inputs/outputs (padrão em UTXO).

---

# **1\) Diferenças arquiteturais importantes (EVM → UTXO)**

* **Estado global vs UTXO imutável**: EVM tem armazenamento mutável; UTXO model não. Em SimplicityHL você modela estado por **state UTXOs** (UTXOs que carregam dados/encerram estado). Cada atualização consome a UTXO antiga e cria uma nova UTXO de estado.

* **Atomicidade**: Transferências múltiplas em uma mesma transação são atômicas — bom. Mas gather inputs pode ser necessário.

* **Identidade de "posição"**: Em EVM, posições são mapeas por endereço+id. Em UTXO, cada posição pode ser representada por um UTXO (ou vários), portanto as operações que mudam uma posição exigem consumir a UTXO que representa essa posição.

* **Custos e limites de script**: SimplicityHL tem restrições de script/size e exec. Projetar UTXOs pequenos e lógica off-chain quando possível.

* **No reentrancy**: UTXO model evita muitos problemas de reentrancy, mas cria novos desafios (ex.: sincronização e race conditions entre quem consome a mesma UTXO).

---

# **2\) Mapeamento dos principais componentes AAVE → SimplicityHL**

| AAVE (EVM) | Função | Equivalente em UTXO/SimplicityHL |
| ----- | ----- | ----- |
| LendingPool | roteia depósitos/ empréstimos, cálculo de juros | **Lending Pool State UTXO** \+ scripts helpers que validam transações que atualizam o estado do pool |
| Reserve (per asset) | parâmetros do asset, taxas | **Reserve State UTXO** por asset (tax strategy, liquidity, indexes) |
| aToken (interest bearing token) | token ERC20 representando depósito | **Asset-backed UTXO token \+ index accounting** ou um token issuance onde saldo muda via mint/burn UTXOs e index guarda rendimento acumulado |
| VariableDebtToken / StableDebtToken | dívida do tomador | **Debt UTXOs** representando posições (principal, borrowIndexAtOpen, rateMode) |
| Interest rate strategy | função para taxas | lógica off-chain em Rate Strategy oracles (também pode ser on-chain na validação do reserve UTXO) |
| LendingPoolCore / Configurator | admin | scripts com multisig UTXOs (admins) |
| Price Oracle | preços | Oracle UTXO(s) com assinaturas |

Observação: preferir **indexing** (cumulative index) para representar juros acumulados em vez de atualizar saldo de todo holder em cada bloco — isso minimiza writes.

---

# **3\) Modelagem de dados (UTXO structures)**

**Reserve UTXO** (por asset)

* asset\_id (asset hash)

* totalLiquidity (in asset units)

* totalVariableDebt (in underlying units)

* totalStableDebt

* liquidityIndex (ray fixed point)

* variableBorrowIndex

* currentLiquidityRate (ray)

* currentVariableBorrowRate (ray)

* reserveFactor

* timestamp (last update)

**Supply aToken representation**

* aToken can be an issued asset where 1 aToken \= share \* liquidityIndex. But in UTXO world, melhor:

  * Keep aToken as a *fungible asset issuance*.

  * When user deposits X underlying \-\> pool mints `a = X / liquidityIndex` aTokens to user (or uses accounting formula)

  * On withdraw, burn aTokens and transfer underlying computed by `a * liquidityIndex`.

**Debt UTXO (per borrower per asset)**

* owner (pubkey hash)

* principal (amount at open)

* borrowIndex (the variableBorrowIndex at the time of borrow)

* stableRate (if stable mode)

* timestamp (last update)  
   This UTXO is consumed and replaced with updated values on repay/partial repay/accrual.

**User Position** can be represented by:

* Multiple UTXOs: one aToken UTXO (balance), one debt UTXO per asset, plus collateral UTXOs (the underlying collateral assets they supplied that are held by pool UTXOs or via aToken ownership).

---

# **4\) Matemática de juros e índices (passo a passo, sem erro)**

Usaremos o padrão AAVE com *cumulative index* (liquidityIndex, borrowIndex). Definir precisão: usar RAY \= 10^27 fixed point.

**Notação**

* `t0` timestamp last update, `t1` current timestamp.

* `rate` \= annual rate in RAY (e.g., 0.03 \* RAY)

* `delta = (t1 - t0) / secondsPerYear` (float rational)

* `index_new = index_old * (1 + rate * delta)` approximately — para maior precisão usar e^(rate \* delta) se quiser compounding contínuo, mas AAVE uses linearization per second with scaled rates. Vamos mostrar a forma discreta simples (AAVE uses more complex continuous compounding). Eu implementaria:

Step by step (discrete continuous approximate):

1. `timeElapsed = t1 - t0` (seconds; compute integer).

2. `ratePerSecond = rate / secondsPerYear` (RAY arithmetic).

3. `indexFactor = 1 + ratePerSecond * timeElapsed` (in RAY fixed point).

4. `index_new = index_old * indexFactor` (RAY multiply).

**Exemplo numérico (digit-by-digit check)**:

* `rate = 5% = 0.05` → as RAY: `0.05 * 10^27 = 5e25`.

* `secondsPerYear = 31536000` (365d).

* `ratePerSecond = 5e25 / 31536000 = 1.586e18 approx` (RAY units).

* If `timeElapsed = 86400` (1 day):

  * `ratePerSecond * timeElapsed ≈ 1.586e18 * 86400 = 1.369e23` (\~0.0001369 in normal).

  * `indexFactor ≈ 1 * 10^27 + 1.369e23 = 1.0001369 * 10^27`.

  * Multiply by `index_old` (also RAY) \-\> new index. Use integer math with exact fixedpoint mul.

**Accrue to a debt position**:

* `currentBorrowBalance = principal * (borrowIndex_current / borrowIndex_at_open)` (both RAY). Implementation: `balance = principal * borrowIndex_current / borrowIndex_at_open`.

This avoids iterating per-user each block.

---

# **5\) Flow das operações (UTXO flows)**

Vou descrever a canonical transaction for each op, com quais UTXOs são consumidos/creados.

## **Deposit (supply)**

Goal: usuário entrega `X` of asset to pool, receives `aTokens` (or increases their aToken balance)  
 Transaction inputs:

* user signs: input UTXO with `X` asset

* pool Reserve UTXO (consumed)  
   Validation (SimplicityHL script checks):

1. Verify deposit input amount matches output to pool.

2. Compute `mintedATokens = X * RAY / liquidityIndex` (or `mint = X / index` with rounding).

3. Create new Reserve UTXO with `totalLiquidity += X; liquidityIndex` (update with accrual using elapsed time); create/mint aToken UTXO to user.  
    Outputs:

* new Reserve UTXO

* aToken UTXO to user (or existing user aToken UTXO replaced)

* change outputs

Note: minting tokens in Liquid may be done via asset issuance or via scripted 'balance UTXO'.

## **Withdraw**

User consumes their aToken UTXO and Reserve UTXO

* Compute `underlying = aTokens * liquidityIndex` (with rounding)

* Burn aTokens and transfer underlying back

* Update Reserve totals

## **Borrow**

User requests to borrow `B` underlying against collateral (collateral may be other assets already supplied; collateral positions must be owned/represented)  
 Transaction consumes:

* Reserve UTXO

* Borrower collateral UTXO(s) (or proof of aToken ownership)

* Possibly existing Debt UTXO  
   Validation:

1. Accrue indices.

2. Check health factor after creating debt: compute `totalCollateralValue` (via oracle prices) and `totalBorrowValue` (including new borrow). health \= Collateral \* liquidationThreshold / totalBorrowValue.

3. If health \> 1 (or some threshold) allow borrow.

4. Create new/updated Debt UTXO with principal increased by `B` and borrowIndex set to `borrowIndex_current`.

5. Transfer underlying asset `B` to borrower (in outputs).

## **Repay**

Consume Debt UTXO and Reserve UTXO and user payment UTXO

* Compute current debt \= principal \* (borrowIndex\_current / borrowIndex\_at\_open)

* Deduct repayment amount; if fully repaid, burn debt UTXO; else replace with smaller principal (recompute borrowIndex\_at\_open \= borrowIndex\_current and new principal \= remainingDebt).

* Update Reserve totals.

## **Liquidation**

Liquidator supplies payment to reduce borrower's debt, seizes collateral.  
 Flow:

* Consumes borrower Debt UTXO, borrower collateral aToken UTXO (or collateral held in pool), Reserve UTXO, and liquidator payment UTXO

* Compute borrower's health (via oracle)

* If health \< 1: allowed.

* Liquidator repays up to `maxCloseable = debt * closeFactor`

* Seize `seizedCollateral = payment * (1 + liquidationBonus) * priceRatio`

* Transfer seized collateral to liquidator, update borrower's debt UTXO (or remove)

* Update Reserve totals

Atomicity is important: all consumed/created in same transaction to prevent race.

---

# **6\) Oráculos de preço**

Design:

* Oracle publishes signed price UTXO(s) per asset pair (price, timestamp, publisherSig).

* Lending scripts validate signature(s) and freshness (price timestamp not older than TTL).

* To avoid single point, accept thresholds (median from multiple oracles) or use a dedicated Oracle aggregator UTXO.

Ataques a mitigar:

* Price manip in DEX — prefer time-weighted average price (TWAP) via feed or Chainlink style aggregator on Liquid.

* Reorg considerations: only accept prices with enough confirmations? But we need fresh prices; weigh tradeoffs.

---

# **7\) Segurança e considerações práticas**

* **Race conditions**: UTXO-based state UTXOs can be raced (two actors see same state UTXO and attempt to consume it). Mitigation:

  * Use well-known "pool manager" off-chain coordinator to assemble transactions (like a relayer).

  * Use short TTL of intended transactions and check nonce-like field in state UTXO.

  * Use optimistic concurrency: transactions will succeed only if they use the current state UTXO (consumed). Loss of attempt results in tx failure, user retries with updated state.

* **UTXO size limits**: Reserve UTXOs may become large. Consider splitting reserves or storing only essential numeric state in the UTXO and storing admin/config off-chain (or in multiple UTXOs).

* **Fee economics**: Many updates require creating transactions that move large values; fees on Liquid are lower than Bitcoin but plan for cost: batch operations, aggregate user ops.

* **Precision / overflow**: Use safe fixed point libraries (RAY/WEI) and check overflows. Use 256-bit integers where possible.

* **Oracles**: Require multi-signed or aggregated oracles to avoid single oracle compromise.

* **Liquid-specific**: Asset issuance and confidentiality — confidential transactions may complicate price checks. For initial MVP, recommend non-confidential UTXOs for state & reserves.

---

# **8\) Test strategy**

1. **Unit tests**: simulate index accrual, borrow/repay math in deterministic environment (python/TS).

2. **Integration tests (local Liquid or regtest)**:

   * Deploy SimplicityHL scripts in regtest cluster.

   * Test sequence: deposit, borrow, time-forward (mine blocks / advance timestamps), accrue interest, repay, partial repay, liquidation.

   * Simulate oracle price manipulation attempts.

3. **Fuzz tests**: random amounts/edgecases (0, max uint, rounding).

4. **Formal verification**: where possible, formally verify invariants (no minting of assets beyond allowed; collateralization invariant; sum of reserves consistent).

5. **Audits**: independent security review of SimplicityHL contracts, focus on arithmetic, signature checks, and oracle validation.

---

# **9\) Esboço de design de contrato em SimplicityHL (pseudocódigo \+ comentários)**

Nota: vou escrever em *pseudo-SimplicityHL* (claro e estruturado) — a ideia é traduzir para a sintaxe exata depois. Em SimplicityHL você tem scripts que validam inputs/outputs — aqui descrevo **conditions** que o script deve checar.

## **Reserve UTXO validation (quando consumida para update)**

Precondições que o script verifica ao consumir `ReserveUTXO_old` e ao criar `ReserveUTXO_new`:

* `new.timestamp > old.timestamp`.

* `new.liquidityIndex == accrueIndex(old.liquidityIndex, old.currentLiquidityRate, new.timestamp - old.timestamp)`.

* `new.variableBorrowIndex == accrueIndex(old.variableBorrowIndex, old.currentVariableBorrowRate, timeElapsed)`.

* `new.totalLiquidity == old.totalLiquidity + netDeposits - netWithdraws`.

* `new.totalVariableDebt == old.totalVariableDebt + netBorrowed - netRepaid`.

* `sum_of_outputs_assets` matches invariant (asset conservation).

* When minting aToken, ensure minted amount equals `netDeposits * RAY / old.liquidityIndex` (formula consistent).

* Helpers: `accrueIndex(index_old, rate, dt)` \= `index_old * (1 + rate * dt / secondsPerYear)` in fixedpoint.

## **Debt UTXO validation (owner-signed)**

When updating debt UTXO:

* Must be signed by borrower (or allow liquidator path with different checks).

* New principal computed consistently: if repay \-\> newPrincipal \= max(0, oldBalance \- repayAmount)  
   where `oldBalance = old.principal * (currentBorrowIndex / old.borrowIndexAtOpen)`.

* If borrow more \-\> newPrincipal \= oldBalance \+ amountBorrowed, and set borrowIndexAtOpen \= currentBorrowIndex.

* For partial updates, set new borrowIndexAtOpen \= currentBorrowIndex and store principal as normalized amount (for subsequent accrual simplification).

## **High-level pseudo-flow de Borrow (validation logic)**

* Inputs: userCollateralProof, ReserveUTXO\_old, DebtUTXO\_old (optional), userBorrowUTXORequest

* Validate Reserve index accrual.

* Compute `borrowable = collateralValue * LTV - existingBorrowValue`.

* Ensure `amountBorrowRequested <= borrowable`.

* Produce ReserveUTXO\_new (increase totalVariableDebt), DebtUTXO\_new (principal increased), transfer asset output to borrower.

(Implement these checks inside SimplicityHL script that enforces signature checks and numeric equalities.)

---

# **10\) Roteiro de implementação (passo-a-passo prático)**

1. **MVP scope**: single asset pool \+ aToken \+ variable rate borrowing \+ repay \+ liquidation \+ single oracle.

2. **Prototype off-chain model**: implemente um simulador em Python/TS com as UTXO transitions para validar lógica de índices e edgecases.

3. **Desenhar layout de UTXO**: Reserve UTXO binary layout \+ Debt UTXO layout \+ Oracle UTXO layout.

4. **Escrever SimplicityHL scripts**:

   * Reserve validator

   * Debt validator

   * Oracle validator (verifica assinatura \+ freshness)

   * Admin multisig script

5. **Deploy em testnet/regtest Liquid** e emitir assets de teste.

6. **Executar testes** (unit/integration/fuzz).

7. **Auditoria** \+ formal checks.

8. **Feature add-ons**: multiple assets, stable rates, liquidity mining, governance.

---

# **11\) Principais riscos & trade-offs (resumo)**

* **Concurrency (UTXO races)** — delays para users ou necessidade de relayer.

* **Precision/rounding** — fixed point carefulness; choose RAY=1e27 as AAVE.

* **Oracle reliability** — multi-sig or aggregator.

* **Transaction fees & UX** — usuários podem precisar pagar tx fees per operation; UX similar a Lightning/coordinator patterns recommended.

* **Confidential transactions** — complicam oráculos e accounting; start with non-confidential.

---

# **12\) Próximos passos práticos (o que eu faria agora se eu fosse você)**

1. Quero que você confirme: **quer que eu gere o pseudocódigo SimplicityHL para `Reserve` e `Debt` validator com campos binários concretos** (layout byte offsets), ou prefere primeiro um simulador em Python/TS que prove as fórmulas?  
    — *Nota: não preciso que você responda agora se preferir que eu escolha — vou assumir que quer o pseudo-código e já preparar.*

2. Se confirmar, eu gero:

   * layout binário (campos com tipos e offsets)

   * scripts SimplicityHL pseudo-code pronto para tradução

   * testes de exemplo (transações simuladas passo-a-passo)

u entrar no modo **engenheiro de software (blockchain)** com foco em **EVM/AAVE** *e* **SimplicityHL / Liquid (UTXO)** e te entregar um plano técnico completo e utilizável para implementar um sistema de lending inspirado na AAVE, adaptado às diferenças fundamentais do modelo UTXO/SimplicityHL. Vou cobrir:

* Diferenças arquiteturais EVM vs UTXO (implicações).

* Mapeamento dos principais componentes da AAVE para construções SimplicityHL.

* Modelagem de dados e tokens (collateral, aTokens, debt positions).

* Matemática de juros e índice acumulado (com passos numéricos).

* Operações principais: deposit, withdraw, borrow, repay, liquidate — com lógica e fluxos UTXO.

* Estratégia de oráculos e atualização de preço.

* Segurança, limites práticos e otimizações (tamanho de UTXO, fees, atomicidade).

* Estrutura de testes e ferramentas / simulações que você deve rodar.

* Um esboço em pseudo-SimplicityHL (blocos lógicos e contratos de estado) — pronto para tradução para código SimplicityHL real.

Vou assumir algumas decisões por pragmatismo (sem te fazer perguntas) — se quiser alterar alguma depois, ajustamos:

**Assunções principais**

1. Rede alvo: Liquid (sidechain com SimplicityHL disponível) — UTXO-based, scripts em SimplicityHL.

2. Existirão tokens representando ativos (pe. tokenized BTC, USDT) compatíveis com Liquid (confiaremos que já há peg-ins/asset issuance).

3. Não vamos implementar todas features AAVE (ex.: governance, incentives complexos) — foco em core lending: depósito (supply), retirada, empréstimo, reembolso, liquidação.

4. Oráculo de preço (externo) fornece preço por pair off-chain \+ assinatura on-chain (ou oracle-UTXO) e será confiável e com alta disponibilidade.

5. Usuários interagirão via transações UTXO assinadas por eles; algumas operações podem requerer um *coordinator* off-chain para juntar inputs/outputs (padrão em UTXO).

---

# **1\) Diferenças arquiteturais importantes (EVM → UTXO)**

* **Estado global vs UTXO imutável**: EVM tem armazenamento mutável; UTXO model não. Em SimplicityHL você modela estado por **state UTXOs** (UTXOs que carregam dados/encerram estado). Cada atualização consome a UTXO antiga e cria uma nova UTXO de estado.

* **Atomicidade**: Transferências múltiplas em uma mesma transação são atômicas — bom. Mas gather inputs pode ser necessário.

* **Identidade de "posição"**: Em EVM, posições são mapeas por endereço+id. Em UTXO, cada posição pode ser representada por um UTXO (ou vários), portanto as operações que mudam uma posição exigem consumir a UTXO que representa essa posição.

* **Custos e limites de script**: SimplicityHL tem restrições de script/size e exec. Projetar UTXOs pequenos e lógica off-chain quando possível.

* **No reentrancy**: UTXO model evita muitos problemas de reentrancy, mas cria novos desafios (ex.: sincronização e race conditions entre quem consome a mesma UTXO).

---

# **2\) Mapeamento dos principais componentes AAVE → SimplicityHL**

| AAVE (EVM) | Função | Equivalente em UTXO/SimplicityHL |
| ----- | ----- | ----- |
| LendingPool | roteia depósitos/ empréstimos, cálculo de juros | **Lending Pool State UTXO** \+ scripts helpers que validam transações que atualizam o estado do pool |
| Reserve (per asset) | parâmetros do asset, taxas | **Reserve State UTXO** por asset (tax strategy, liquidity, indexes) |
| aToken (interest bearing token) | token ERC20 representando depósito | **Asset-backed UTXO token \+ index accounting** ou um token issuance onde saldo muda via mint/burn UTXOs e index guarda rendimento acumulado |
| VariableDebtToken / StableDebtToken | dívida do tomador | **Debt UTXOs** representando posições (principal, borrowIndexAtOpen, rateMode) |
| Interest rate strategy | função para taxas | lógica off-chain em Rate Strategy oracles (também pode ser on-chain na validação do reserve UTXO) |
| LendingPoolCore / Configurator | admin | scripts com multisig UTXOs (admins) |
| Price Oracle | preços | Oracle UTXO(s) com assinaturas |

Observação: preferir **indexing** (cumulative index) para representar juros acumulados em vez de atualizar saldo de todo holder em cada bloco — isso minimiza writes.

---

# **3\) Modelagem de dados (UTXO structures)**

**Reserve UTXO** (por asset)

* asset\_id (asset hash)

* totalLiquidity (in asset units)

* totalVariableDebt (in underlying units)

* totalStableDebt

* liquidityIndex (ray fixed point)

* variableBorrowIndex

* currentLiquidityRate (ray)

* currentVariableBorrowRate (ray)

* reserveFactor

* timestamp (last update)

**Supply aToken representation**

* aToken can be an issued asset where 1 aToken \= share \* liquidityIndex. But in UTXO world, melhor:

  * Keep aToken as a *fungible asset issuance*.

  * When user deposits X underlying \-\> pool mints `a = X / liquidityIndex` aTokens to user (or uses accounting formula)

  * On withdraw, burn aTokens and transfer underlying computed by `a * liquidityIndex`.

**Debt UTXO (per borrower per asset)**

* owner (pubkey hash)

* principal (amount at open)

* borrowIndex (the variableBorrowIndex at the time of borrow)

* stableRate (if stable mode)

* timestamp (last update)  
   This UTXO is consumed and replaced with updated values on repay/partial repay/accrual.

**User Position** can be represented by:

* Multiple UTXOs: one aToken UTXO (balance), one debt UTXO per asset, plus collateral UTXOs (the underlying collateral assets they supplied that are held by pool UTXOs or via aToken ownership).

---

# **4\) Matemática de juros e índices (passo a passo, sem erro)**

Usaremos o padrão AAVE com *cumulative index* (liquidityIndex, borrowIndex). Definir precisão: usar RAY \= 10^27 fixed point.

**Notação**

* `t0` timestamp last update, `t1` current timestamp.

* `rate` \= annual rate in RAY (e.g., 0.03 \* RAY)

* `delta = (t1 - t0) / secondsPerYear` (float rational)

* `index_new = index_old * (1 + rate * delta)` approximately — para maior precisão usar e^(rate \* delta) se quiser compounding contínuo, mas AAVE uses linearization per second with scaled rates. Vamos mostrar a forma discreta simples (AAVE uses more complex continuous compounding). Eu implementaria:

Step by step (discrete continuous approximate):

1. `timeElapsed = t1 - t0` (seconds; compute integer).

2. `ratePerSecond = rate / secondsPerYear` (RAY arithmetic).

3. `indexFactor = 1 + ratePerSecond * timeElapsed` (in RAY fixed point).

4. `index_new = index_old * indexFactor` (RAY multiply).

**Exemplo numérico (digit-by-digit check)**:

* `rate = 5% = 0.05` → as RAY: `0.05 * 10^27 = 5e25`.

* `secondsPerYear = 31536000` (365d).

* `ratePerSecond = 5e25 / 31536000 = 1.586e18 approx` (RAY units).

* If `timeElapsed = 86400` (1 day):

  * `ratePerSecond * timeElapsed ≈ 1.586e18 * 86400 = 1.369e23` (\~0.0001369 in normal).

  * `indexFactor ≈ 1 * 10^27 + 1.369e23 = 1.0001369 * 10^27`.

  * Multiply by `index_old` (also RAY) \-\> new index. Use integer math with exact fixedpoint mul.

**Accrue to a debt position**:

* `currentBorrowBalance = principal * (borrowIndex_current / borrowIndex_at_open)` (both RAY). Implementation: `balance = principal * borrowIndex_current / borrowIndex_at_open`.

This avoids iterating per-user each block.

---

# **5\) Flow das operações (UTXO flows)**

Vou descrever a canonical transaction for each op, com quais UTXOs são consumidos/creados.

## **Deposit (supply)**

Goal: usuário entrega `X` of asset to pool, receives `aTokens` (or increases their aToken balance)  
 Transaction inputs:

* user signs: input UTXO with `X` asset

* pool Reserve UTXO (consumed)  
   Validation (SimplicityHL script checks):

1. Verify deposit input amount matches output to pool.

2. Compute `mintedATokens = X * RAY / liquidityIndex` (or `mint = X / index` with rounding).

3. Create new Reserve UTXO with `totalLiquidity += X; liquidityIndex` (update with accrual using elapsed time); create/mint aToken UTXO to user.  
    Outputs:

* new Reserve UTXO

* aToken UTXO to user (or existing user aToken UTXO replaced)

* change outputs

Note: minting tokens in Liquid may be done via asset issuance or via scripted 'balance UTXO'.

## **Withdraw**

User consumes their aToken UTXO and Reserve UTXO

* Compute `underlying = aTokens * liquidityIndex` (with rounding)

* Burn aTokens and transfer underlying back

* Update Reserve totals

## **Borrow**

User requests to borrow `B` underlying against collateral (collateral may be other assets already supplied; collateral positions must be owned/represented)  
 Transaction consumes:

* Reserve UTXO

* Borrower collateral UTXO(s) (or proof of aToken ownership)

* Possibly existing Debt UTXO  
   Validation:

1. Accrue indices.

2. Check health factor after creating debt: compute `totalCollateralValue` (via oracle prices) and `totalBorrowValue` (including new borrow). health \= Collateral \* liquidationThreshold / totalBorrowValue.

3. If health \> 1 (or some threshold) allow borrow.

4. Create new/updated Debt UTXO with principal increased by `B` and borrowIndex set to `borrowIndex_current`.

5. Transfer underlying asset `B` to borrower (in outputs).

## **Repay**

Consume Debt UTXO and Reserve UTXO and user payment UTXO

* Compute current debt \= principal \* (borrowIndex\_current / borrowIndex\_at\_open)

* Deduct repayment amount; if fully repaid, burn debt UTXO; else replace with smaller principal (recompute borrowIndex\_at\_open \= borrowIndex\_current and new principal \= remainingDebt).

* Update Reserve totals.

## **Liquidation**

Liquidator supplies payment to reduce borrower's debt, seizes collateral.  
 Flow:

* Consumes borrower Debt UTXO, borrower collateral aToken UTXO (or collateral held in pool), Reserve UTXO, and liquidator payment UTXO

* Compute borrower's health (via oracle)

* If health \< 1: allowed.

* Liquidator repays up to `maxCloseable = debt * closeFactor`

* Seize `seizedCollateral = payment * (1 + liquidationBonus) * priceRatio`

* Transfer seized collateral to liquidator, update borrower's debt UTXO (or remove)

* Update Reserve totals

Atomicity is important: all consumed/created in same transaction to prevent race.

---

# **6\) Oráculos de preço**

Design:

* Oracle publishes signed price UTXO(s) per asset pair (price, timestamp, publisherSig).

* Lending scripts validate signature(s) and freshness (price timestamp not older than TTL).

* To avoid single point, accept thresholds (median from multiple oracles) or use a dedicated Oracle aggregator UTXO.

Ataques a mitigar:

* Price manip in DEX — prefer time-weighted average price (TWAP) via feed or Chainlink style aggregator on Liquid.

* Reorg considerations: only accept prices with enough confirmations? But we need fresh prices; weigh tradeoffs.

---

# **7\) Segurança e considerações práticas**

* **Race conditions**: UTXO-based state UTXOs can be raced (two actors see same state UTXO and attempt to consume it). Mitigation:

  * Use well-known "pool manager" off-chain coordinator to assemble transactions (like a relayer).

  * Use short TTL of intended transactions and check nonce-like field in state UTXO.

  * Use optimistic concurrency: transactions will succeed only if they use the current state UTXO (consumed). Loss of attempt results in tx failure, user retries with updated state.

* **UTXO size limits**: Reserve UTXOs may become large. Consider splitting reserves or storing only essential numeric state in the UTXO and storing admin/config off-chain (or in multiple UTXOs).

* **Fee economics**: Many updates require creating transactions that move large values; fees on Liquid are lower than Bitcoin but plan for cost: batch operations, aggregate user ops.

* **Precision / overflow**: Use safe fixed point libraries (RAY/WEI) and check overflows. Use 256-bit integers where possible.

* **Oracles**: Require multi-signed or aggregated oracles to avoid single oracle compromise.

* **Liquid-specific**: Asset issuance and confidentiality — confidential transactions may complicate price checks. For initial MVP, recommend non-confidential UTXOs for state & reserves.

---

# **8\) Test strategy**

1. **Unit tests**: simulate index accrual, borrow/repay math in deterministic environment (python/TS).

2. **Integration tests (local Liquid or regtest)**:

   * Deploy SimplicityHL scripts in regtest cluster.

   * Test sequence: deposit, borrow, time-forward (mine blocks / advance timestamps), accrue interest, repay, partial repay, liquidation.

   * Simulate oracle price manipulation attempts.

3. **Fuzz tests**: random amounts/edgecases (0, max uint, rounding).

4. **Formal verification**: where possible, formally verify invariants (no minting of assets beyond allowed; collateralization invariant; sum of reserves consistent).

5. **Audits**: independent security review of SimplicityHL contracts, focus on arithmetic, signature checks, and oracle validation.

---

# **9\) Esboço de design de contrato em SimplicityHL (pseudocódigo \+ comentários)**

Nota: vou escrever em *pseudo-SimplicityHL* (claro e estruturado) — a ideia é traduzir para a sintaxe exata depois. Em SimplicityHL você tem scripts que validam inputs/outputs — aqui descrevo **conditions** que o script deve checar.

## **Reserve UTXO validation (quando consumida para update)**

Precondições que o script verifica ao consumir `ReserveUTXO_old` e ao criar `ReserveUTXO_new`:

* `new.timestamp > old.timestamp`.

* `new.liquidityIndex == accrueIndex(old.liquidityIndex, old.currentLiquidityRate, new.timestamp - old.timestamp)`.

* `new.variableBorrowIndex == accrueIndex(old.variableBorrowIndex, old.currentVariableBorrowRate, timeElapsed)`.

* `new.totalLiquidity == old.totalLiquidity + netDeposits - netWithdraws`.

* `new.totalVariableDebt == old.totalVariableDebt + netBorrowed - netRepaid`.

* `sum_of_outputs_assets` matches invariant (asset conservation).

* When minting aToken, ensure minted amount equals `netDeposits * RAY / old.liquidityIndex` (formula consistent).

* Helpers: `accrueIndex(index_old, rate, dt)` \= `index_old * (1 + rate * dt / secondsPerYear)` in fixedpoint.

## **Debt UTXO validation (owner-signed)**

When updating debt UTXO:

* Must be signed by borrower (or allow liquidator path with different checks).

* New principal computed consistently: if repay \-\> newPrincipal \= max(0, oldBalance \- repayAmount)  
   where `oldBalance = old.principal * (currentBorrowIndex / old.borrowIndexAtOpen)`.

* If borrow more \-\> newPrincipal \= oldBalance \+ amountBorrowed, and set borrowIndexAtOpen \= currentBorrowIndex.

* For partial updates, set new borrowIndexAtOpen \= currentBorrowIndex and store principal as normalized amount (for subsequent accrual simplification).

## **High-level pseudo-flow de Borrow (validation logic)**

* Inputs: userCollateralProof, ReserveUTXO\_old, DebtUTXO\_old (optional), userBorrowUTXORequest

* Validate Reserve index accrual.

* Compute `borrowable = collateralValue * LTV - existingBorrowValue`.

* Ensure `amountBorrowRequested <= borrowable`.

* Produce ReserveUTXO\_new (increase totalVariableDebt), DebtUTXO\_new (principal increased), transfer asset output to borrower.

(Implement these checks inside SimplicityHL script that enforces signature checks and numeric equalities.)

---

# **10\) Roteiro de implementação (passo-a-passo prático)**

1. **MVP scope**: single asset pool \+ aToken \+ variable rate borrowing \+ repay \+ liquidation \+ single oracle.

2. **Prototype off-chain model**: implemente um simulador em Python/TS com as UTXO transitions para validar lógica de índices e edgecases.

3. **Desenhar layout de UTXO**: Reserve UTXO binary layout \+ Debt UTXO layout \+ Oracle UTXO layout.

4. **Escrever SimplicityHL scripts**:

   * Reserve validator

   * Debt validator

   * Oracle validator (verifica assinatura \+ freshness)

   * Admin multisig script

5. **Deploy em testnet/regtest Liquid** e emitir assets de teste.

6. **Executar testes** (unit/integration/fuzz).

7. **Auditoria** \+ formal checks.

8. **Feature add-ons**: multiple assets, stable rates, liquidity mining, governance.

---

# **11\) Principais riscos & trade-offs (resumo)**

* **Concurrency (UTXO races)** — delays para users ou necessidade de relayer.

* **Precision/rounding** — fixed point carefulness; choose RAY=1e27 as AAVE.

* **Oracle reliability** — multi-sig or aggregator.

* **Transaction fees & UX** — usuários podem precisar pagar tx fees per operation; UX similar a Lightning/coordinator patterns recommended.

* **Confidential transactions** — complicam oráculos e accounting; start with non-confidential.

---

# **12\) Próximos passos práticos (o que eu faria agora se eu fosse você)**

1. Quero que você confirme: **quer que eu gere o pseudocódigo SimplicityHL para `Reserve` e `Debt` validator com campos binários concretos** (layout byte offsets), ou prefere primeiro um simulador em Python/TS que prove as fórmulas?  
    — *Nota: não preciso que você responda agora se preferir que eu escolha — vou assumir que quer o pseudo-código e já preparar.*

2. Se confirmar, eu gero:

   * layout binário (campos com tipos e offsets)

   * scripts SimplicityHL pseudo-code pronto para tradução

   * testes de exemplo (transações simuladas passo-a-passo)

# **SimplicityHL — Esqueleto completo: Reserve Validator & Debt Validator**

Documento técnico e pseudo-código pronto para tradução para SimplicityHL real.  
 Inclui: layout byte-a-byte dos UTXOs, funções aritméticas (RAY fixed point), validações, fluxos de transação exemplo, vetores de teste simples, e prompts para iniciar um repositório com Git Spec Kit \+ WindSurf.

---

## **Sumário**

1. Objetivo

2. Convenções numéricas e definições

3. Layouts (byte-a-byte)

   * Reserve UTXO

   * Debt UTXO

   * aToken UTXO (resumo)

   * Oracle UTXO (resumo)

4. Biblioteca utilitária (pseudo-SimplicityHL)

   * Operações em RAY

   * accrualIndex

   * safeMul, safeDiv, checkedAdd/Sub

5. Reserve Validator — especificação e pseudo-código

   * Invariants checados

   * Fluxos suportados (deposit, withdraw, borrow, repay, accrue)

6. Debt Validator — especificação e pseudo-código

   * Invariants checados

   * Fluxos suportados (openBorrow, partialRepay, fullRepay, liquidate)

7. Exemplos de transação (UTXO inputs/outputs)

8. Vetores numéricos de teste (digit-by-digit) — sanity checks

9. Recomendações de implementação e limitações

10. Testes & roteiro

11. Prompts para Git Spec Kit \+ WindSurf

---

## **1\) Objetivo**

Gerar um esqueleto pronto para um desenvolvedor traduzir para SimplicityHL. O foco cobre dois validadores centrais:

* **Reserve Validator**: mantém e atualiza o estado global de uma reserva por asset (liquidez, índices, taxas).

* **Debt Validator**: gerencia posições de dívida do tomador (principal normalizado, índice de abertura, etc.).

Também inclui funções aritméticas fix-point (RAY \= 10^27) e layouts binários para UTXOs.

---

## **2\) Convenções numéricas e definições**

* **RAY** \= 10^27 (padrão AAVE). Todos os índices e taxas são guardados em RAY.

* **secondsPerYear** \= 31\_536\_000 (365 dias). Usado para converter taxa anual para taxa por segundo.

* **uint256** semantics: todos os inteiros são não-negativos; operações verificam overflow/underflow.

* **Arredondamento**: quando necessário, usar arredondamento *down* para evitar mint indesejado (floor). Documentar pontos onde se usa round-up (ex.: cálculo de `seizedCollateral` para beneficiar liquidator — aí usar ceil apropriadamente).

Terminologia:

* `liquidityIndex` (RAY): fator que converte `aToken` balance \-\> underlying. `underlying = aAmount * liquidityIndex / RAY`.

* `variableBorrowIndex` (RAY): fator para normalizar debt principal.

* `principal` in Debt UTXO: *normalized* principal expressed relative to borrowIndexAtOpen (see math below).

---

## **3\) Layouts (byte-a-byte)**

Todos os layouts assumem encoding **big-endian** para inteiros fixos. Os offsets abaixo são bytes a partir do início do `scriptData` (rede Liquid permite attach data no UTXO). Os tamanhos são em bytes.

### **3.1 Reserve UTXO (conteúdo do state UTXO)**

Total size: 1 header \+ 32 \* N fields \=\> próximo de 320 bytes (depende campos extras).

| Offset | Size (B) | Nome | Tipo | Descrição |
| ----- | ----- | ----- | ----- | ----- |
| 0 | 1 | version | u8 | versão do layout (ex: 0x01) |
| 1 | 20 | asset\_id | bytes20 | asset identifier (ex: asset hash / ticker tag) — escolha o tamanho que preferir (20 usado aqui) |
| 21 | 32 | totalLiquidity | uint256 | soma do underlying disponível (em units do asset) |
| 53 | 32 | totalVariableDebt | uint256 | soma das dívidas variáveis (underlying units) |
| 85 | 32 | liquidityIndex | uint256 (RAY) | index para converts aToken \<-\> underlying |
| 117 | 32 | variableBorrowIndex | uint256 (RAY) | index usado para normalizar dívidas |
| 149 | 32 | currentLiquidityRate | uint256 (RAY) | taxa anual aplicada aos depositantes |
| 181 | 32 | currentVariableBorrowRate | uint256 (RAY) | taxa anual aplicada aos borrowers |
| 213 | 32 | reserveFactor | uint256 (RAY) | fração que vai para o reserve (ex: 0.1 \* RAY) |
| 245 | 8 | lastUpdateTimestamp | uint64 | epoch seconds |
| 253 | 8 | decimals | u64 | número de decimais do asset (por compatibilidade) |
| 261 | variable | extraFlags | varbytes | flags: pausado, borrowingEnabled, usageAsCollateralEnabled etc. (opcional) |

Observações:

* Usar 32 bytes (256-bit) para valores monetários e índices para prevenir overflow.

* `asset_id` pode ser adaptado ao identificador nativo do Liquid (32 bytes) — aqui usamos 20 para compactação; ajuste conforme rede.

### **3.2 Debt UTXO (por posição do usuário por asset)**

Total size: \~128 bytes.

| Offset | Size | Nome | Tipo | Descrição |
| ----- | ----- | ----- | ----- | ----- |
| 0 | 1 | version | u8 | layout version |
| 1 | 20 | ownerPubKeyHash | bytes20 | identificador do borrower |
| 21 | 32 | principal | uint256 | principal normalizado (see math) |
| 53 | 32 | borrowIndexAtOpen | uint256 (RAY) | variableBorrowIndex when position opened/last normalized |
| 85 | 32 | stableRate | uint256 (RAY) | se aplicável, 0 se não |
| 117 | 8 | lastUpdateTimestamp | uint64 | epoch |
| 125 | 3 | flags | u8\[3\] | e.g., rateMode bit, frozen etc. |

Notas:

* `principal` armazena valor que, quando multiplicado por `currentBorrowIndex / borrowIndexAtOpen` dá o currentDebt.

* Owner deve assinar ou prover prova de posse conforme script.

### **3.3 aToken UTXO (resumo)**

* aToken pode ser um asset issuance. Em vez de grandes dados on-chain, mantemos holdings via asset tokens. Caso prefira script-driven balance UTXO, manter um layout similar a este para representar balances.

### **3.4 Oracle UTXO (resumo)**

* layout: version | asset\_id | price (uint256, price in quote asset with decimals normalized to 1e18) | timestamp | publisherPubKey | signature

---

## **4\) Biblioteca utilitária (pseudo-SimplicityHL)**

Abaixo estão funções que você deve implementar em SimplicityHL *ou* garantir que a biblioteca de runtime ofereça.

**Nota de segurança**: SimplicityHL limite expressões complexas, então implemente operações pesadas off-chain quando possível. Porém, validações essenciais (consistência de índices e invariants) devem estar no validator.

### **4.1 Constantes**

RAY \= 10\*\*27

SECONDS\_PER\_YEAR \= 31536000

### **4.2 safeMul(a,b) \-\> (ok, result)**

* checa overflow `if b != 0 and result / b != a -> fail`.

* return floor(a \* b)

### **4.3 rayMul(a,b) \-\> (ok,res)**

* compute floor(a \* b / RAY)

* implement via safeMul \+ safeDivRoundingDown

### **4.4 rayDiv(a,b) \-\> (ok,res)**

* compute floor(a \* RAY / b)

* check b\!=0

### **4.5 accrueIndex(indexOld, rate\_RAY, deltaSeconds) \-\> indexNew**

Pseudocode (integers):

\# rate\_RAY is annual rate in RAY

ratePerSecond \= rayDiv(rate\_RAY, SECONDS\_PER\_YEAR \* RAY) ???

\# clearer: ratePerSecond\_RAY \= rate\_RAY / SECONDS\_PER\_YEAR (but keep in RAY)

ratePerSecond\_RAY \= floor(rate\_RAY / SECONDS\_PER\_YEAR)

\# indexFactor \= 1 \+ ratePerSecond\_RAY \* deltaSeconds

indexFactor\_RAY \= RAY \+ floor(ratePerSecond\_RAY \* deltaSeconds)

indexNew \= rayMul(indexOld, indexFactor\_RAY)

**Implementation note**: perform operations in order to avoid loss of precision. Use 512-bit intermediate if possible; otherwise split.

### **4.6 getCurrentBorrowBalance(principal\_normalized, borrowIndexAtOpen, borrowIndexCurrent)**

\# debt \= principal\_normalized \* borrowIndexCurrent / borrowIndexAtOpen

temp \= rayMul(principal\_normalized, borrowIndexCurrent)

debt \= floor(temp / borrowIndexAtOpen)  \# or use rayDiv but principal wasn't in RAY necessarily

Detalhes de normalização: se `principal` foi guardado já como `principal = actualDebt * RAY / borrowIndexAtOpen` então:  
 `actualDebt = rayMul(principal, borrowIndexCurrent)`.  
 Escolha uma convenção e seja consistente (na spec abaixo usamos `principal` armazenado tal que `actualDebt = rayMul(principal, borrowIndexCurrent)`).

---

## **5\) Reserve Validator — especificação e pseudo-código**

O validator garante que qualquer transação que consuma uma `ReserveUTXO_old` e gere uma `ReserveUTXO_new` respeite invariants e faça contabilidade correta.

### **5.1 Invariants chaves (sempre checar)**

1. `new.lastUpdateTimestamp > old.lastUpdateTimestamp`.

2. `new.liquidityIndex == accrueIndex(old.liquidityIndex, old.currentLiquidityRate, delta)`.

3. `new.variableBorrowIndex == accrueIndex(old.variableBorrowIndex, old.currentVariableBorrowRate, delta)`.

4. `new.totalVariableDebt == old.totalVariableDebt + netBorrowed - netRepaid` (respecting rounding).

5. `new.totalLiquidity == old.totalLiquidity + netDeposits - netWithdraws + netFees`.

6. Conservation of assets: total underlying asset in inputs \== total underlying asset in outputs (modulo fees burned/collected to reserveAddress).

7. When minting/burning aToken, minted amount equals `netDeposits * RAY / old.liquidityIndex` (or formula inversa, check convention).

8. `new.currentLiquidityRate` and `new.currentVariableBorrowRate` can only be changed by admin or recalculated deterministically by rate strategy (se tiver on-chain). Se a pool atualiza as rates, a transação deve provar a origem (admin signature or deterministic function inputs).

### **5.2 Funções auxiliares (no validator)**

* `computeMintedATokens(deltaDeposit)` \-\> uses `liquidityIndex` pre-accrual or post-accrual? Definir claramente: usar index *após* accrual para evitar desbalance.

### **5.3 Pseudocódigo — entrada/saída do validator**

\# inputs: ReserveUTXO\_old, zero-or-more user asset inputs, optional DebtUTXOs, optional OracleUTXO, signatures...

\# outputs: ReserveUTXO\_new, user asset outputs, minted aToken outputs, fee outputs

function reserve\_validator(Reserve\_old, Reserve\_new, txContext):

  \# 1\. timestamps

  delta \= Reserve\_new.lastUpdateTimestamp \- Reserve\_old.lastUpdateTimestamp

  require(delta \> 0\)

  \# 2\. accrual checks

  expectedLiquidityIndex \= accrueIndex(Reserve\_old.liquidityIndex, Reserve\_old.currentLiquidityRate, delta)

  require(Reserve\_new.liquidityIndex \== expectedLiquidityIndex)

  expectedVariableBorrowIndex \= accrueIndex(Reserve\_old.variableBorrowIndex, Reserve\_old.currentVariableBorrowRate, delta)

  require(Reserve\_new.variableBorrowIndex \== expectedVariableBorrowIndex)

  \# 3\. compute net movements from txContext

  netDeposits \= sum\_incoming\_underlying\_to\_reserve \- sum\_outgoing\_underlying\_from\_reserve\_to\_users

  netBorrows \= sum\_outgoing\_underlying\_to\_users \- sum\_incoming\_underlying\_from\_users\_for\_repay

  netFees \= sum\_fees\_collected\_in\_tx

  \# 4\. totals

  require(Reserve\_new.totalLiquidity \== Reserve\_old.totalLiquidity \+ netDeposits \+ netFees \- netWithdraws)

  require(Reserve\_new.totalVariableDebt \== Reserve\_old.totalVariableDebt \+ netBorrows \- netRepaid)

  \# 5\. mint/burn aTokens check

  mintedA \= computeMintAmount(netDeposits, Reserve\_old.liquidityIndex)  \# or use Reserve\_new index definition

  require(mintedA \== sum\_of\_aToken\_outputs\_minted)

  \# 6\. asset conservation (underlying)

  require(totalUnderlyingInInputs \== totalUnderlyingInOutputs \+ feesBurned)

  \# 7\. rate updates

  if txClaimsRateChange:

    require(adminSignedOrDeterministic( ... ))

  return true

end

**Notas de implementação**:

* `txContext` deve ser extraído da transação (inputs/outputs amounts) e classificado por asset type.

* Em SimplicityHL, implementar `require` com `fail` que cancela a transação.

---

## **6\) Debt Validator — especificação e pseudo-código**

O Debt Validator aceita atualizações de uma Debt UTXO (ou criação) e verifica consistência.

### **6.1 Invariants**

1. `ownerPubKeyHash` deve assinar a autorização para operações que alterem a dívida (exceto ações de liquidator, nas quais liquidator provê prova/assinatura própria e valida o estado HEALTH \< 1).\`

2. `new.principal` deve ser calculado de acordo com operação (borrow increases, repay decreases) e manter a relação com `borrowIndex`/`borrowIndexAtOpen`.

3. `lastUpdateTimestamp` aumenta.

4. Em repay, os fundos do pagador (repayer input) devem ser consumidos na quantia apropriada.

### **6.2 Fluxos**

* **OpenBorrow**: cria Debt UTXO com `principalNormalized = computeNormalizedPrincipal(amountBorrowed, borrowIndexCurrent)` e `borrowIndexAtOpen = borrowIndexCurrent`.

* **PartialRepay**: calcula currentDebt \= rayMul(principalStored, borrowIndexCurrent); newDebt \= currentDebt \- repayAmount; store new principal \= floor(newDebt \* RAY / borrowIndexCurrent) and set borrowIndexAtOpen \= borrowIndexCurrent.

* **FullRepay**: repayAmount \>= currentDebt \-\> no Debt UTXO emitted (burn/close); excess payment returned to payer.

* **Liquidate**: liquidator path not requiring borrower signature. Validator allows consumption if: health \< 1 (needs oracle), payment amount matches, seized collateral computed correctly, outputs to liquidator equal seized collateral.

### **6.3 Pseudocódigo**

function debt\_validator(Debt\_old, Debt\_new\_opt, txContext):

  \# identify caller role (owner, liquidator, admin)

  if txContext.signedBy(Debt\_old.owner):

    role \= BORROWER

  else if txContext.includes(liquidatorSignature):

    role \= LIQUIDATOR

  else:

    fail

  \# get current borrowIndex from Reserve UTXO included in txContext (must be present)

  borrowIndexCurrent \= txContext.reserve.variableBorrowIndex

  deltaT \= txContext.currentTimestamp \- Debt\_old.lastUpdateTimestamp

  require(deltaT \>= 0\)

  currentDebt \= rayMul(Debt\_old.principal, borrowIndexCurrent)

  if role \== BORROWER:

    if txContext.containsBorrowRequest:

      amount \= txContext.borrowAmount

      \# check borrow allowed (collateral health) by reading collateral positions and oracle

      require(checkHealthAfterBorrow(...))

      newPrincipalNormalized \= floor((currentDebt \+ amount) \* RAY / borrowIndexCurrent)

      emit Debt\_new with principal \= newPrincipalNormalized, borrowIndexAtOpen \= borrowIndexCurrent

    else if txContext.containsRepay:

      repayAmount \= txContext.repayAmount

      newDebt \= max(0, currentDebt \- repayAmount)

      if newDebt \== 0:

         \# close debt: no Debt\_new

      else:

         newPrincipalNormalized \= floor(newDebt \* RAY / borrowIndexCurrent)

         emit Debt\_new with principal \= newPrincipalNormalized, borrowIndexAtOpen \= borrowIndexCurrent

  else if role \== LIQUIDATOR:

    \# require health \< 1 (oracle)

    require(checkHealth(Debt\_old.owner) \< 1\)

    \# compute maxCloseable \= currentDebt \* closeFactor

    \# compute seizedCollateral \= computeSeizedCollateral(repayAmount, priceRatio, liquidationBonus)

    require(outputsToLiquidator \== seizedCollateral)

    \# adjust debt accordingly

  return true

end

**Observação**: `rayMul(Debt_old.principal, borrowIndexCurrent)` pressupõe que `principal` foi armazenado em forma "normalized": principalNormalized that when multiplied by borrowIndexCurrent yields the actual debt. AAVE usa convenções específicas — escolha a que sua implementação seguirá e mantenha a documentação consistente.

---

## **7\) Exemplos de transação (UTXO inputs/outputs)**

### **7.1 Deposit (usuário deposita 1\_000 units)**

Inputs:

* userAssetUTXO: 1\_000 underlying (signed by user)

* ReserveUTXO\_old  
   Outputs:

* ReserveUTXO\_new (totalLiquidity \+= 1\_000, indices updated)

* aTokenUTXO\_to\_user: mintedATokens \= floor(1\_000 \* RAY / reserve.liquidityIndex\_old)

* change outputs (fees)

A validação garante que mintedATokens corresponde à equação e que conservation of asset holds.

### **7.2 Borrow 500 (usuário toma emprestado)**

Inputs:

* ReserveUTXO\_old

* BorrowerCollateralProof UTXOs (ex.: aToken ownership proof)

* optional DebtUTXO\_old

* borrower signature  
   Outputs:

* ReserveUTXO\_new (totalVariableDebt \+= 500, totalLiquidity \-= 500\)

* DebtUTXO\_new (principalNormalized computed accordingly)

* underlying asset 500 to borrower

---

## **8\) Vetores numéricos de teste (digit-by-digit)**

**Teste 1 — accrual index**

* index\_old \= RAY (1 \* 10^27)

* rate \= 5% \= 0.05 \* RAY \= 5e25

* delta \= 86400 (1 dia)

Calcule:

1. ratePerSecond\_RAY \= floor(rate / SECONDS\_PER\_YEAR) \= floor(5e25 / 31536000\)

   * 5e25 / 31536000 \= 158578553... \* 10^12? Vamos calcular com precisão simbólica:

   * Use integer division: 5e25 // 31536000 \= 158578553... (result in RAY units)

2. indexFactor\_RAY \= RAY \+ ratePerSecond\_RAY \* 86400

3. indexNew \= floor(index\_old \* indexFactor\_RAY / RAY) \= floor(1e27 \* indexFactor\_RAY / 1e27) \= indexFactor\_RAY

Se quiser vetores exatos com todos dígitos, gerar script Python/TS para confirmar; no documento incluí fórmula exata para replicar.

**Teste 2 — debt normalization**

* borrowIndexAtOpen \= 1e27

* borrowIndexCurrent \= 1.0001369e27 (após 1 dia a 5% a.a.)

* principalNormalized \= floor(actualDebt \* RAY / borrowIndexCurrent)

* actualDebt esperado \= rayMul(principalNormalized, borrowIndexCurrent)

Recomenda-se rodar testes automatizados em python para checar dígito-a-dígito.

---

## **9\) Recomendações de implementação e limitações**

* **Escolha da convenção de normalization**: duas estratégias comuns:

  * (A) armazenar `principalNormalized = actualDebt * RAY / borrowIndexAtOpen`. Vantagem: `currentDebt = rayMul(principalNormalized, borrowIndexCurrent)` (simples)

  * (B) armazenar `principalAtOpen` e `borrowIndexAtOpen`. Depois compute `currentDebt = principalAtOpen * borrowIndexCurrent / borrowIndexAtOpen` (pode exigir um extra division). Escolha A para menor operação no validator.

* **Off-chain relayers**: para evitar fails por race conditions, ofereça um relayer que monte transações corretamente reunindo inputs/UTXOs dos usuários.

* **Oracle design**: preferir um aggregator multi-sig ou median of time-window. Validator deve checar timestamp \<= TTL.

* **Gas / cpu**: SimplicityHL tem limites de custo de execução. Mantenha cálculos pequenos; prefira pré-calcular valores off-chain e provar com merkle commitments se necessário.

---

## **10\) Testes & roteiro**

1. Implementar simulador em Python (UTXO engine minimal): Reserve state, Debt state, index accrual logic.

2. Unit tests: accrual, borrow/repay, rounding, edgecases (zero, 1 wei, large values).

3. Integration: deploy scripts em Liquid regtest; fazer transações reais end-to-end.

4. Fuzz: inputs aleatórios para tentar quebrar invariants.

5. Security review: revisão de arithmetic, assinaturas, oracle handling.

---

## **11\) Prompts para Git Spec Kit \+ WindSurf**

Abaixo há prompts prontos para gerar um repositório inicial com Git Spec Kit (padrão de repositório) e configurar WindSurf (tooling de desenvolvimento/CI). Use-os com seu assistente generator de repositórios (ex.: Git Spec Kit CLI) ou cole em issue/README.

### **11.1 Prompt: gerar repositório base (Git Spec Kit)**

\# Prompt: "Crie um repositório Git estruturado para desenvolvimento de contratos SimplicityHL de um sistema de lending (Reserve & Debt validators).

\# Requisitos:

\- Linguagem: README, scripts de build (Makefile), testes em Python (pytest), pasta \`simplicity/\` com pseudo-code e \`specs/\` com layouts binários.

\- CI: GitHub Actions com job que roda linter de Python e testes unitários; job que valida a formatação dos arquivos de spec.

\- Templates: ISSUE\_TEMPLATE para bugs e feature requests; PR\_TEMPLATE com checklist (security, tests, docs).

\- Licença: Apache-2.0

\- Estrutura sugerida:

  \- /README.md

  \- /LICENSE

  \- /Makefile

  \- /simplicity/reserve\_validator.simp (pseudocode)

  \- /simplicity/debt\_validator.simp

  \- /simulator/python/\* (simulador e testes)

  \- /specs/layouts.md

  \- /.github/workflows/ci.yml

\- Incluir scripts: \`make test\`, \`make lint\`, \`make sim\` (roda o simulador)

Return: arquivo ZIP do repositório ou instruções passo-a-passo para criar via Git Spec Kit CLI.

"

### **11.2 Prompt: configurar WindSurf (ambiente local para SimplicityHL dev)**

\# Prompt: "Configurar projeto WindSurf para desenvolvimento e teste de SimplicityHL.

\# Requisitos:

\- Integração com o repositório gerado acima.

\- Tasks: build (compila pseudo-scripts), run-sim (executa simulador python), run-regtest (opcional: levantar node Liquid regtest via docker-compose), test (pytest), format (prettier/black), ci (roda tudo em GH Actions).

\- Fornecer arquivo windsurf.config.json com tasks e env vars para regtest endpoints.

\- Adicionar snippets VSCode para executar tasks WindSurf.

Return: windsurf.config.json and example tasks and README steps.

"

### **11.3 Template de README inicial (resumo rápido para o repositório)**

* Título: `simplicity-lending`

* Badges: build passing, license

* Descrição curta: "Esqueleto de contrato de lending inspirado em AAVE, implementado para UTXO/SimplicityHL (Reserve & Debt validators)."

* Como começar: `make setup`, `make sim`.

* Onde definir parâmetros: `specs/layouts.md`.

* Como contribuir: issue template \+ PR checklist.

---

## **Observações finais e entregáveis**

* Este documento é um **esqueleto técnico** pronto para tradução em código SimplicityHL.

* Eu **não** reproduzi sintaxe exata de SimplicityHL pois existem variações de toolchain; o pseudo-código foi pensado para ser direto de traduzir: expressões `rayMul`, `accrueIndex`, `require` se mapeiam para combinadores SimplicityHL e verificações booleans.

* Próximo passo sugerido por mim (se desejar): gerar o repositório inicial com Git Spec Kit \+ WindSurf automaticamente com os arquivos base (README, Makefile, scripts de pseudocódigo e simulador Python) — posso gerar agora os arquivos e um ZIP no workspace.

---

### **Créditos**

Autor: Assistente (modo: engenheiro de software — blockchain, EVM/AAVE \+ SimplicityHL)  
 Data: 2025-11-06

\*\*\* FIM DO DOCUMENTO \*\*\*

