# THE SPINE — memory that changes what an agent does

**NEURAL_MESH × Sibyl Memory** · [Public repository](https://github.com/D0xedDevi0/dejavu-sibyl-memory) · MIT

> A persistent memory layer for autonomous risk agents: turn recorded experience into guarded decisions, shared capability, and auditable action evidence.

**Watch:** [THE SPINE canonical demo](demo/_v3/demo_the_spine_v3.mp4) — 2:13, narrated, and rebuilt from the current proof path. The older `demo/demo_the_spine.mp4` remains historical only. See [video audit](docs/audit-surfaces.md) and the [final demo script](docs/final-demo-script.md).

**Judge shortcut:** [claim → implementation → test → evidence](docs/judge.md) · [final audit and release checklist](docs/FINAL_AUDIT.md).

## Run the fresh-process deletion proof

From the repository root, in Python 3.11+ with `uv` installed:

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e '.[test]' && PATH="$PWD/.venv/bin:$PATH" DEJAVU_DRY_RUN=1 bash demo/run_continuous_gate.sh
```

This runs separate Python processes against a disposable Sibyl database:

```text
Session A: persist a structured crisis lesson, then exit
Session B: open the same database, recall the lesson → equity 0.024 (printed as 0.02)
Control: delete only that disposable memory store
Session C: same market frame, fresh process, no lesson → equity 0.55
```

The full proof frame (including volatility and yield slope) gives 0.024 equity; the simpler `dejavu --crisis` frame gives 0.05. Do not mix their displayed values.

These are deterministic policy allocations in a demonstration, **not executed portfolio trades**. The lesson and market frame are fixtures; the experiment proves dependence on persisted memory, not discovery of a profitable investment strategy. The no-memory branch deliberately falls back to a naive book. Production deployment should abstain or fail closed instead.

## Three reproduced measurements

The final audit reran these experiments from a clean source archive with freshly installed declared dependencies. [Raw outputs](docs/evidence/final/ablations.txt).

🟦 **Fresh recall lowers equity below 0.05; deleting memory restores 0.55.** Source: `policy.decide_differently`; tests: `tests/test_loadbearing.py`.

🟦 **7.072 percentage points of simulated mean loss averted.** `demo/ablation_benchmark.py`: 200 seeded frames, 150 stressed, mean model return −2.828% with memory versus −9.900% without; 75% of decisions change.

🟦 **3/3 selected recall-blind fixtures are caught by the distilled rule; 0/3 by first-act recall.** `demo/conscience_ablation.py`: six constructed episodes, not an independent held-out market benchmark or a general safety guarantee.

Secondary experiment: `demo/spine_ablation.py` preserves **0.8176 versus 0.4887** of normalized starting capital, a **1.67× remaining-capital ratio**. Despite its legacy `crises: 12` JSON field, the code runs **12 periods: six crisis periods alternating with six zero-return calm periods**. Its −1.650% / −5.625% means average all 12 periods. Do not call those per-crisis means or realized investment returns. It differs from the 200-frame experiment and must not be merged with it.

## Architecture: one store, multiple decision mechanisms

```text
structured experience → Sibyl SQLite/FTS5 → fresh-process recall → policy proposal
                             │                                  │
                             ├── provenance / hard lessons ─────┤
                             ├── UNKNOWN / THIN → learning plan │
                             └── shared specialist board        ▼
                                                       guard / approved book
                                                                │
                                                   symbolic Base action adapter
```

The **Sibyl SDK is actually used**: `MemoryClient.local`, `set_entity`, `search`, journal, state, reference and archive operations. No vector database or account is required for local tests. `from dejavu import Memory` exposes the public library surface; [agent integration examples](docs/AGENTS.md) show how to reuse it.

Memory influence is bounded: lexical recall and stored provenance affect deterministic rules. This is not an LLM trading agent, a trained LoRA, or a generic retrieval leaderboard claim. Learner skill proposals and threshold distillation are code-level learning mechanisms, not model-weight training.

## Safety and knowledge gaps

🟦 `guard.guard_book` returns allow/warn/block from stored hard lessons and the proposed exposure. See the final code audit for execution-boundary wiring and receipt semantics.
🟦 `meta.known_unknowns` labels COVERED / THIN / UNKNOWN. `curriculum.learn_plan` schedules gaps; acquiring a lesson can close them. UNKNOWN does not automatically imply that every caller abstains.
🟦 `exchange.import_lesson` checks artifact integrity, scans for tested poison patterns, and gates writes. A matching hash proves integrity, **not truth or a trusted author**; the scanner is not a universal prompt-injection defense.
🟦 `consensus.reach_consensus` limits duplicate-owner votes and records deadlock. It relies on supplied owner identity; it is not permissionless Sybil resistance or proof of independent humans.
🟦 `consent.request_wipe` refuses unforced deletion and records forced wipes in a separate audit file. It is an application policy, not filesystem access control; direct file deletion remains possible.

Tests: `test_meta_guard_exchange.py`, `test_consensus_curriculum.py`, `test_poison_sybil_hardening.py`, `test_distill_consent.py`.

## Partner evidence — keep the claims narrow

### Base: historical execution evidence

`src/dejavu/base_action.py` maps the policy to a **1,000-wei symbolic ETH transfer**, not a token swap, portfolio rebalance, or hedge. A transaction hash returned by broadcasting alone is not confirmation; inspect its receipt. The two historical action hashes below/previously cited are self-transfers, so they do not validate the current fee-recipient branch or the new Guard wiring.

🟦 Historical action: [0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a](https://basescan.org/tx/0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a).
🟦 Historical root anchor: [0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7](https://basescan.org/tx/0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7).

The anchor is a content commitment in transaction data, not an NFT mint or a contract-enforced ownership right. Recomputing a matching root needs the corresponding snapshot. An old anchor does not authenticate every later layer description or current database state.

### x402: paid static proof snapshot

[Endpoint](https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query) · source: `demo/x402/memory-query.ts`.

The handler returns **hard-coded snapshot metadata**, including an anchor reference, layer descriptions and historical benchmark values. It does **not** query this repository's live SQLite store, cryptographically prove the entire response, or verify `asset_resolves` on each request. HTTP 402 proves a payment challenge, not successful delivery or customer demand.

Historical settlement references:

🟦 [0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5](https://basescan.org/tx/0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5)
🟦 [0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93](https://basescan.org/tx/0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93)

Inspect USDC Transfer logs to identify the **economic payer**; the transaction sender can be a relayer. Decoded Transfer logs confirm both payments came from our own agent wallet, through the facilitator to our endpoint wallet: self-funded tests, not an independent customer or proven product-market fit. [Commercial evidence and limitations](docs/pmf.md).

### Virtuals: implemented, not included in the default claim

Registration, ACP job and provider artifacts exist. The local `virtuals.exercise()` function checks signer metadata; it is not itself a completed paid ACP job. Claim **Base only** in the submission copy unless final public job evidence and the canonical video satisfy the organizer's partner requirement. No multiplier is guaranteed by this repository. See [public-surface audit](docs/audit-surfaces.md).

## Product and market

Target buyer: an operator running restartable autonomous workers that must carry risk lessons, constraints and provenance across sessions. The proposed paid unit is a verified decision receipt or a memory-review service—not a generic chatbot subscription.

The narrow pilot: compare the same worker with and without persisted reviewed lessons; measure repeated incidents, unsafe proposals blocked, false blocks, human overrides, and time to recover after restart. A named external design partner and repeat usage remain **unverified**, not claimed PMF. D0xedDev infrastructure is prior operator context, not proof that THE SPINE is already deployed throughout that platform.

## Reproducibility

```bash
.venv/bin/python -m pytest -o addopts='' -q
.venv/bin/python -m pytest -o addopts='' -v tests/test_loadbearing.py tests/test_fleet.py tests/test_ablation.py tests/test_spine_ablation.py tests/test_conscience_ablation.py
DEJAVU_DRY_RUN=1 .venv/bin/dejavu --crisis
DEJAVU_DRY_RUN=1 .venv/bin/dejavu-fleet --crisis
DEJAVU_DRY_RUN=1 .venv/bin/dejavu-sovereign --crisis
```

Run destructive controls only on disposable demo databases; the shell proof creates one for that purpose. Normal demos may write beneath `data/`; do not point them at production memory. Benchmark rendering needs system DejaVu fonts; video rebuilding also needs FFmpeg. Optional sibling NEURAL_MESH backend tests may skip if that package is absent. The audited baseline was **142 passing tests**; the final report records the post-change count rather than leaving a stale count in every document.

## Prior work and eligibility

Git history begins **August 17, 2026**, before the stated September 1–10 build window. Persistence, policy, Base execution, fleet, initial layers, paid-read experiments and earlier films already existed in August. September commits add L9–L16, public APIs, conscience ablation, ACP provider work and hardening.

**Do not describe all Sibyl integration as new during the window.** Preserve history and obtain organizer clarification on eligibility of the pre-window prototype. MacroBench policy and broader D0xedDev/NEURAL_MESH infrastructure are also prior work. The final local audit changes are not public until separately authorized and published.

## Detailed sixteen-layer reference

L1 Sovereign · L2 Identity · L3 Dream · L4 Commons · L5 Regret · L6 Temporal · L7 Sovereign Loop · L8 Conflict · L9 Discernment · L10 Meta · L11 Guard · L12 Exchange · L13 Consensus · L14 Curriculum · L15 Distill · L16 Consent.

[Judge matrix](docs/judge.md) is the factual reference. [Doctrine](docs/doctrine.md) is narrative framing, not a security or consciousness claim. Earlier plans in `BUILD_SPEC.md`, `CONCEPT.md`, `LANES.md` and `docs/UPGRADES.md` are explicitly historical and do not establish readiness.
