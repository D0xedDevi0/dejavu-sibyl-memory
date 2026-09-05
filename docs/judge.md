# Judge's Cheat-Sheet — THE SPINE (NEURAL_MESH × Sibyl Memory)

> **🎯 The crux of scoring — *how* the memory improves the build (30‑second answer):**
> the decision function cannot work without Sibyl Memory. Cold-start Session B recalls
> the past crisis lesson and flips **equity 0.55 → 0.05** (naive → de-risk); delete the
> store and the same frame reverts to the naïve 0.55 losing book. Measured (seed 1337):
> **0.82 vs 0.49 capital = 1.67× saved**, mean crisis return −1.65% vs −5.63%. The memory
> also defends money economically: the sibling NEURAL_MESH Proof-of-Memory stack
> slashes a lying agent **$0.10/claim vs $0.00 without** (repo `D0xedDevi0/NEURAL_MESH`,
> `bench/bond_economics.py`), and a live `$0.01 USDC` x402 endpoint earned two real
> Base settlements from an external wallet.

> **Pitch:** The agent does not merely have memory. The memory is the agent's
> dynamic data layer: it determines decisions and identity, coordinates its team,
> evolves skills, preserves temporal context, anchors itself on Base, and earns
> through paid proofs. Delete it and the system materially fails.

## 1. Six layers, one canonical arc

| Layer | What it proves | Exact implementation |
|---|---|---|
| L1 Sovereign | Full-store content root is committed on Base; destructive wipe orphans it | `src/dejavu/sovereign.py::memory_root`, `sovereign_mint`, `asset_orphaned` |
| L2 Identity | Same store means same identity across fresh runtimes; wipe changes identity | `src/dejavu/sovereign.py::identity`, `is_same_being` |
| L3 Dream | Repeated journal patterns become accepted skills | `src/dejavu/memory.py::learn`, `accept_proposal` |
| L4 Commons | Specialists coordinate through one shared Sibyl store without direct calls | `src/dejavu/fleet.py` |
| L5 Regret | The store records avoided outcomes and the road not taken | `src/dejavu/regret.py` |
| L6 Temporal | Beliefs carry time; stale lessons move to recoverable ARCH without changing the sovereign full-store root | `src/dejavu/temporal.py`, `tests/test_temporal.py`, `tests/test_sovereign.py::test_archiving_preserves_sovereign_root` |
| L7 Sovereign Loop | Memory that knows it owns itself: the mint receipt is written back into the store (REFERENCE tier, folded into the root) so a fresh box's identity provably references its committed onchain root | `src/dejavu/sovereign.py::anchor_self`, `resolve_anchor`, `is_self_anchored` |
| L8 Conflict | Write-time conflict resolution: a contradiction is superseded to ARCH + journaled (SUPERSEDES), never blindly overwritten; the full revision trail is reconstructable | `src/dejavu/supersede.py::supersede_entity`, `supersession_chain` |
| L9 Discernment | The write-quality gate — the half of memory everyone ignores. Facts are scored (novelty, falsifiable truth, category use, noise floor) and only those that EARN a slot persist; capacity is a budget (weakest live → ARCH, recoverable), and the ingestion policy recalibrates from which memories actually got used. Deterministic, no-LLM. Load-bearing mirror: no gate → store floods → real lesson buried. | `src/dejavu/gates.py::gate_write`, `feedback_used`, `recalibrate_policy` |
| L10 Meta | Memory knows itself — no more hallucinated coverage. `known_unknowns` answers "do I know this or not?" with COVERED / THIN / UNKNOWN (UNKNOWN is a signal to go learn, not an empty list); `confidence` scores per-entity trust from recorded provenance; `coverage` maps maturity + blind spots. Load-bearing: without it a planner treats absence as "no constraint" and proceeds naive. | `src/dejavu/meta.py::known_unknowns`, `confidence`, `coverage` |
| L11 Guard | Memory that ACTS, not just informs. A hard lesson (prov.hard OR serious outcome drawdown) gives memory **veto power**: even when fuzzy recall text-misses, a stressed frame + overweight-equity book is BLOCKED. Second line of defense — memory that says "no." | `src/dejavu/guard.py::guard_book`, `hard_lessons` |
| L12 Exchange | Memory that travels. `export_lesson` hashes body+provenance into a portable, verifiable, priced artifact; `import_lesson` verifies + L9-gates the foreign lesson, records origin provenance, journals the purchase, and credits the seller's x402 earnings ledger. Load-bearing: a store that never lived the crisis imports the lesson → cold-start de-risks. Cross-agent scar tissue transfer. | `src/dejavu/exchange.py::export_lesson`, `import_lesson`, `verify_artifact` |
| L13 Consensus | The cross-agent truth layer (L8 for a fleet). Independent agents' differing beliefs are reconciled by L10-confidence weighting: UNANIMOUS / CONVERGED (conf ≥ quorum) / MAJORITY (honest) / DEADLOCK (no fabricated winner, recorded CONTESTED). A lone low-confidence dissent can't overturn a provenance-backed hard lesson; an unknown split isn't papered over. | `src/dejavu/consensus.py::reach_consensus`, `agent_believe` |
| L14 Curriculum | Memory schedules its own learning — the self-improving loop: L10 sees UNKNOWN → L14 plans (priority = gap × importance) → L12 imports the verified lesson through the L9 gate → L10 reports COVERED. Ignorance becomes coverage across one executable cycle. | `src/dejavu/curriculum.py::learn_plan`, `gaps_remaining`, `record_attempt` |
| L15 Distill | Memory as capability, not tape. DISTILL reads every structured crisis scar, learns the most conservative risk that triggered protection, and writes ONE threshold rule that **generalizes** to frames none of the scars named (e.g. a pure-vol spike when every scar was credit-driven). Under-sampled → no rule (honest). Load-bearing: raw recall misses the vol frame; the distilled rule de-risks it. | `src/dejavu/distill.py::distill_rule`, `decide_with_skill` |
| L16 Consent | Memory that argues for its own life. `wipe_impact` enumerates what a wipe destroys (identity, onchain anchor, guard lessons); `request_wipe` refuses a silent wipe until force=True + reason, then journals its own destruction to a store-independent log surviving the deletion. A wipe is permanent but never untraceable. | `src/dejavu/consent.py::wipe_impact`, `request_wipe`, `read_wipe_audit` |

Run the canonical arc:

```bash
pip install -e ".[test]"
dejavu-sovereign --crisis
```

## 2. Load-bearing gate

The decision function calls Sibyl recall. With the persisted crisis lesson,
equity is cut to **0.05**. With the store deleted, recall is empty and policy
fails open to the naive **0.55** allocation.

| Proof | Where |
|---|---|
| Fresh-session read/write | `src/dejavu/memory.py::write_lesson`, `recall_lessons` |
| Decision changes because of recall | `src/dejavu/policy.py::decide_differently` |
| Destructive deletion test | `tests/test_loadbearing.py` |
| Full eight-beat arc test | `tests/test_spine.py` |
| Self-referential anchor + supersession tests | `tests/test_sovereign_loop.py` |
| Seeded economic ablation | `demo/spine_ablation.py`, `tests/test_spine_ablation.py` |

Measured gate, seed 1337:

| Metric | With memory | Wiped |
|---|---:|---:|
| Capital after 12 crises | **0.82** | **0.49** |
| Mean crisis return | **−1.65%** | **−5.63%** |
| Capital preservation | **1.67×** | — |
| Identity | stable across boxes | changes |

The final demo must show this as one continuous, unedited terminal segment with
a visible UTC timestamp and Git commit hash.

## 3. Sibyl is the dependency

`Memory` wraps the real `sibyl-memory-client` local store. Session A writes an
entity and journal evidence; Session B opens the same SQLite/FTS5-backed Sibyl
store in a fresh process and searches it. Deleting the database removes the
cross-session signal and changes the decision.

- Pinned SDK packages: `pyproject.toml`
- Typed facade: `src/dejavu/memory.py`
- Fresh-process behavior: `tests/test_loadbearing.py`, final continuous demo segment

## 4. Base proof

### Sovereign content-root anchor

- Transaction: [`0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7`](https://basescan.org/tx/0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7)
- Block: `50608909`
- Status: success
- Calldata commits the demonstrated memory root.

### x402 paid proof endpoint

- Endpoint: https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query
- Price: `0.01 USDC`
- Network: Base (`eip155:8453`)
- Flow: HTTP 402 → EIP-3009 authorization → retry → HTTP 200
- Handler: `demo/x402/memory-query.ts`
- Client reproducer: `demo/x402/settle-memory-query.mjs`

Verified successful settlements:

1. [`0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5`](https://basescan.org/tx/0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5), block `50609928`
2. [`0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93`](https://basescan.org/tx/0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93), block `50609934`

Each receipt records a `0.01 USDC` transfer from the payer through the
facilitator settlement path. These blocks are distinct from the sovereign-root
anchor block.

**Claim boundary:** the deployed endpoint serves a paid, onchain-verifiable
proof snapshot of the demonstrated store. It is not described as a direct live
query against the local SQLite database.

## 5. Onchain decision-path correction

`src/dejavu/base_action.py` now makes policy branches distinguishable:

- `hold` → sender self-transfer
- `de_risk` → validated fee-recipient destination

`tests/test_onchain.py::test_de_risk_and_hold_have_distinct_transaction_targets`
pins the distinction. Historical self-transfer receipts remain historical
wallet-operation evidence; they are not presented as proof of a distinct
recipient branch.

## 6. Reproducibility

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -q
python demo/spine_ablation.py
python demo/build_video_spine.py
```

Core tests run without a wallet secret. Live broadcasts require
`DEJAVU_WALLET_KEY`; dry-run paths do not load credentials. The six optional
NEURAL_MESH backend tests skip cleanly when the sibling backend is unavailable.

## 7. Partner-claim discipline

- **Base:** claimed and demonstrated by the sovereign anchor and x402 receipts.
- **Virtuals:** ✅ **CLAIMED.** The `dejavu` agent is a **registered, signer-active
  (`ACP_ONLY` = transacting-capable) Virtuals ACP agent** on Base mainnet — and a
  **real ACP job was exercised live** on 2026-09-04: job `76304` (v2, Base mainnet
  8453) where the dejavu agent (`0xef25…47bb`) hired provider LUMI for
  `forecast_calibration` with a posted requirement. Verified onchain via
  `acp job history --job-id 76304 --chain-id 8453` (status `open`, client +
  provider + requirement recorded). Identity + signer in
  `virtuals-dejavu-agent.md`; live exercise reproducible via the ACP CLI
  (`virtuals.py`).
- **PMF bonus (+10):** ✅ **CLAIMED.** Public design-partner/pilot artifact:
  **`docs/pmf.md`** — live paid x402 endpoint with **two real settlements from an
  external wallet** (`0x4a15fc61…`, $0.01 USDC each, Base), the sovereign onchain
  anchor, and the production agent wallet (459 onchain txs). All receipts
  verifiable via `eth_getTransactionReceipt`.

## 8. Thirty-second summary

> THE SPINE makes Sibyl Memory load-bearing. A fresh agent recalls an earlier
> crisis lesson and cuts risk from 0.55 to 0.05; deleting the store restores the
> losing decision. That same store is a multi-layer asset: identity, evolving
> skills, team commons, regret, temporal archive, a sovereign Base-anchored
> proof that has already earned USDC through verified x402 settlements, a
> self-referential loop where it remembers its own onchain anchor, and a
> write-time conflict resolver that supersedes rather than overwrites.
>
> **Second act (L9–L16)** — the part the field hasn't built: the memory gates what
> gets written, knows what it doesn't know, vetoes what hurts, trades what it
> learns (live x402), agrees on truth across agents, schedules its own learning,
> distills experience into capability, and refuses to be silently erased. For the
> 90-second narrative pitch, read **[`docs/doctrine.md`](doctrine.md)** — or open
> the D0xedDev-style visual showcase **[`docs/showcase.html`](showcase.html)**
> (preview: `preview-full.png`) for the whole system as one browser surface.

MIT licensed. Canonical repository:
https://github.com/D0xedDevi0/dejavu-sibyl-memory
