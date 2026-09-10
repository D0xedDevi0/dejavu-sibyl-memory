# THE SPINE — canonical judge-proof matrix

**Read first:** [README](../README.md) → fresh-process deletion proof → this matrix. [Final audit](FINAL_AUDIT.md) records the tested revision and release blockers. Historical documentation is not current verification.

## The core proof

Session A persists a structured fixture lesson in real Sibyl SQLite/FTS5. It exits. A new process recalls the lesson and changes the same-frame allocation to **0.024 equity** (printed as 0.02). Delete only that disposable store; another fresh process returns **0.55**. This establishes a causal dependence on persisted memory, not profitable trading or general model intelligence.

```bash
PYTHON=.venv/bin/python DEJAVU_DRY_RUN=1 bash demo/run_continuous_gate.sh
.venv/bin/python -m pytest -o addopts='' -v tests/test_loadbearing.py tests/test_fleet.py
```

## Claims, code, tests and evidence

Canonical video: [`demo/_v3/demo_the_spine_v3.mp4`](../demo/_v3/demo_the_spine_v3.mp4), measured at 133.523220 seconds (2:13), with h264 video and AAC narration. The continuous fresh-process proof is rendered from captured gate output; card values are generated from real local execution. The older `demo/demo_the_spine.mp4` is historical only and is not the submission artifact.

| Claim | Exact implementation | Executable test | Evidence / public target | Existing video timestamp | Status / confusion risk |
|---|---|---|---|---|---|
| Persist and recall in Sibyl | `src/dejavu/memory.py::write_lesson`, `recall_lessons`, `search` | `tests/test_recall.py`; `tests/test_loadbearing.py` | `demo/continuous_gate.py`; final execution log | See video audit; do not substitute animation | Real SDK; fixture lesson, not live market discovery |
| Same frame changes because memory exists | `src/dejavu/policy.py::decide_differently`; `demo/continuous_gate.py::recall_phase` | `tests/test_loadbearing.py` | `demo/run_continuous_gate.sh` subprocess experiment | See video audit | 0.024 loaded / 0.55 wiped; simplified CLI frame gives 0.05; deliberate unsafe baseline, not production fallback |
| Guard evaluates hard lessons | `src/dejavu/guard.py::guard_book`, `hard_lessons` | `tests/test_meta_guard_exchange.py`; final receipt tests in code audit | [Code audit](audit-code.md), dry-run receipt | New receipt not in historical film | Scope depends on caller wiring; no universal execution firewall |
| Shared-memory fleet | `src/dejavu/fleet.py::fleet_alloc_decide`, `read_board` | `tests/test_fleet.py` | `dejavu-fleet --crisis` / wipe control | Not asserted in canonical film | Specialist functions, not evidence of independent LLM workers |
| Learner produces skills | `src/dejavu/memory.py::learn`, `accept_proposal` | `tests/test_recall.py`; `tests/test_public_surface.py` | `dejavu --crisis --learn` dry-run | See video audit | Structured skill generation; no LoRA or model-weight training |
| Content identity and Base anchor | `src/dejavu/sovereign.py::memory_root`, `identity`, `sovereign_mint` | `tests/test_sovereign.py` | [Historical anchor](https://basescan.org/tx/0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7) | See video audit | Transaction-data commitment, not token ownership; snapshot needed for root verification |
| Regret and temporal archive | `src/dejavu/regret.py`; `src/dejavu/temporal.py` | `tests/test_spine.py`; `tests/test_temporal.py` | `dejavu-sovereign --crisis` | Not asserted | Counterfactual outcomes are supplied/modelled, not observed alternate history |
| Anchor recall and supersession | `sovereign.anchor_self`, `resolve_anchor`; `supersede.supersede_entity`, `supersession_chain` | `tests/test_sovereign_loop.py` | Sibyl reference/archive entries | See video audit | Self-reference is metadata, not consciousness or permanent snapshot availability |
| Write-quality gates | `src/dejavu/gates.py::gate_write`, `recalibrate_policy` | `tests/test_gates.py` | CLI L9 output | No new-film timestamp verified | Deterministic heuristics, not truth verification |
| Known gaps cause learning plans | `meta.known_unknowns`; `curriculum.learn_plan`, `gaps_remaining` | `tests/test_consensus_curriculum.py`; `tests/test_public_surface.py::test_autonomous_agent_self_improves` | UNKNOWN → plan → acquired lesson → COVERED | No new-film timestamp verified | Coverage heuristic; planning is not autonomous external acquisition |
| Portable lesson integrity / tested poison rejection | `exchange.export_lesson`, `verify_artifact`, `import_lesson` | `tests/test_meta_guard_exchange.py`; `tests/test_poison_sybil_hardening.py` | Local export/import and refusal journal | No new-film timestamp verified | Hash is not signature/author authentication; scan is not comprehensive |
| Owner-diverse consensus and deadlock | `consensus.reach_consensus`, `agent_believe` | `tests/test_consensus_curriculum.py`; `tests/test_poison_sybil_hardening.py` | Local independent stores and specified owners | No new-film timestamp verified | Supplied owners need trustworthy identity outside demo |
| Distillation catches selected recall misses | `distill.distill_rule`, `decide_with_skill` | `tests/test_distill_consent.py`; `tests/test_conscience_ablation.py` | [Rerun output](evidence/final/ablations.txt): 3/3 selected novel frames | Not in August film | Small constructed panel; not broad out-of-distribution safety |
| Audited application wipe | `consent.request_wipe`, `wipe_impact`, `read_wipe_audit` | `tests/test_distill_consent.py` | Sidecar audit survives intentional wipe | Not in August film | Filesystem owner can bypass API and delete sidecar |
| Memory-derived Base action | `base_action.execute`, `_transaction_target` | `tests/test_onchain.py`; final execution tests | [Historical action](https://basescan.org/tx/0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a) | See video audit | Symbolic dust ETH transfer, NOT a hedge/rebalance; old tx does not prove new Guard path |
| Paid snapshot rail | `demo/x402/memory-query.ts` | Read-only HTTP challenge + historical USDC receipts | [Endpoint](https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query) | See video audit | Static metadata, not live SQLite; HTTP 402 is not a paid response |
| Virtuals partner work | `src/dejavu/virtuals.py::exercise`; ACP artifacts | `tests/test_virtuals.py` checks local integration only | [Surface audit](audit-surfaces.md) | Existing final film does not establish September ACP work | Base-only default claim; registration/signer status is not fulfilled job |
| Commercial demand | No independent customer implementation/test | None | [PMF evidence limits](pmf.md) | Old external-payer assertion must be corrected | Unproven; relayer transaction sender is not necessarily economic customer |

## Measurements: separate experiments

1. **200-frame ablation:** 150 stressed frames, seeded sampling. Mean model returns −2.828% versus −9.900%; 7.072 percentage points averted; 75% changed decisions.
2. **Spine sequence:** six crises alternating with six calm zero-return periods. Final normalized capital 0.8176 versus 0.4887. Reported means −1.650% versus −5.625% average all twelve periods. A 1.67× ratio of remaining capital is not “1.67× profit.”
3. **Conscience panel:** six hand-constructed episodes, three selected recall-blind cases. Distilled-rule arm catches all three; first-act recall catches none. This does not isolate all sixteen layers independently.

All values reproduced in [raw output](evidence/final/ablations.txt). Returns are from declared toy P&L functions, not historical market backtests or realized trades.

## Thirty-second pitch

> A restarted worker should not repeat the same mistake because its conversation disappeared. THE SPINE writes experience into Sibyl, recalls it in a new process, and changes the decision. Remove only the memory and the decision reverts. Hard lessons can constrain proposals; knowledge gaps become learning plans; shared stores coordinate specialists. The prototype adds symbolic Base execution and paid snapshot evidence. Its next product milestone is a measured external operator pilot—not an unsupported claim of production market fit.

## Release rule

Do not mark submission ready solely because local tests pass. The public revision, video proof, qualifying posts, build-window eligibility and saved submission state must each be checked. No final-audit change has been published by this pass.
