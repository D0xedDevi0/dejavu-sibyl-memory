# NEURAL_MESH × Sibyl Memory — LANES (novel, unexplored build directions)

**Goal:** don't build the obvious single-agent "memory-echo" demo everyone will
submit. Create lanes that *haven't been done* — each grounded in verified Sibyl
capability and our real onchain/agent stack. Winner = one that clears the
load-bearing gate AND hits the innovation band (25 pts) harder than the field.

Verified substrate (all confirmed against client 0.6.1):
- Multi-tenant shared-file store: several agents write/read the SAME memory.db,
  isolated per tenant, in one file -> **blackboard / fleet coordination**. ✅
- 5-tier schema (HOT/WARM/COLD/REF/ARCH) -> hot state, warm facts, cold audit.
- Learner: journal patterns -> skill proposals the agent accepts (self-learning).
- Hermes adapter (SibylMemoryProvider) -> native Hermes memory backend.
- Base onchain: x402 escrow 0x055280, wallet key, feeRecipient 0xf8f96d.
- We ranked #2 on MacroBench arena with a regime book (reusable substrate).

---

## LANE 1 — "THE FLEET" (multi-agent blackboard, shared memory)  ⭐ TOP PICK
**Not one agent that remembers — a TEAM of agents coordinated by one shared
memory.** Each specialist agent (news, allocator, onchain-executor, risk) reads
the same Sibyl store, writes its read of the world to a shared board, and every
fresh session picks up the FLEET's accumulated state — not just its own.

- **Load-bearing:** delete the shared store -> the fleet has no coordination;
  no agent sees another's output -> the system collapses into isolated agents.
- **Innovation:** shared-memory coordination is the thing the rubric's
  "innovation / multi-agent" band explicitly rewards, and most submissions are
  single-agent. We'd be the blackboard-fleet entry.
- **Onchain:** allocator's fleet-informed decision -> real Base x402 action.
- **Virtuals:** the fleet = multiple ACP jobs / registered agents coordinating.
- **Demo beat:** "Three agents. One brain. Delete the brain and the team falls
  apart." Split-screen two fresh sessions.

## LANE 2 — "MEMORY AS CASH" (load-bearing memory = the wallet)
Memory IS the asset: an agent whose recall is a *permission* to act onchain.
No recall -> no x402 payment -> the onchain action literally cannot fire.
- **Load-bearing:** the transaction's *authorization* comes from a recalled
  memory record (a signed lesson / approved counterparty list in Sibyl).
- **Innovation:** memory as an onchain gating layer — "you only pay what you
  remember." Fuses memory + payments into one dependency.
- **Base:** x402 quote/execute gated on a Sibyl recall. Strong story.

## LANE 3 — "AUDIT IMMORTALITY" (COLD journal as the product)
The append-only COLD journal becomes the deliverable — a tamper-evident
decision ledger an agent emits for every onchain action. Load-bearing because
"no record, no action" (mirrors Sibyl Sovereign's rule).
- **Innovation:** turns memory into *accountability/compliance*, not just recall.
- **Base:** every decision -> journaled -> then executed; README shows the
  immutable trail. Strong for judges who care about agent accountability.

## LANE 4 — "THE AGENT THAT SELF-EVOLVES" (Learner as the core)
Lean on the **Learner**: the agent mines its own journal, proposes skills, and
ACCEPTS them — so it literally rewrites its own behavior across sessions.
- **Load-bearing:** its decision policy is the accepted skill proposals living
  in memory; delete them -> it reverts to a blank policy.
- **Innovation:** self-modifying agent via its own memory. Few will build the
  full accept-loop. Pairs naturally with LANE 1 (fleet members evolve skills).

## LANE 5 — "RECALL-DRIVEN REGIME AGENT" (the honest version of what we have)
Single-agent memory-echo trading (our MacroBench book) — the SAFE, well-
understood lane. Good, but most likely crowded. Keep as fallback/floor.

---

## Recommendation
**LANE 1 "THE FLEET"** as the headline (highest innovation + cleanest
load-bearing + natural Base/Virtuals fit), with **LANE 4 (self-evolving
Learner)** as the finishing mechanic inside it — the fleet members learn and
update shared skills. This is the chariot lane: multi-agent, shared-memory,
self-improving, onchain. Not done, and it showcases Sibyl's *deepest* features
(multi-tenant, learner, journal) instead of just `set_entity`/`search`.

**If time is tight:** LANE 5 alone clears the gate; but the whole point is to
advance — go Fleet.

## Verified building blocks to reuse
- **Fleet = ONE shared tenant + namespace-by-name.** Cross-tenant reads are NOT
  exposed (search/list are tenant-scoped) — so the blackboard uses a single
  `tenant_id="fleet-brain"` with namespaced entity names (`view/news/market`,
  `view/risk/stress`). ✅ PROVEN in proto/fleet.py (allocator cold-start reads
  the whole board, de-risks; wipe -> naive 0.60).
- `MemoryClient.local(path, tenant_id=...)` / `set_tenant()`.
- `Learner(storage, max_proposals_per_run=N).run()` + accept_proposal().
- `SibylMemoryProvider(require_credentials=False)` for Hermes-native agents.
- MacroBench regime book as the allocator's decision substrate.
- Prototype: `proto/fleet.py` (Lane 1) and `proto/echo_loop.py` (Lane 5).
