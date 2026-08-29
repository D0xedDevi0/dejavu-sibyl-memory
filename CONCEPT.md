# NEURAL_MESH × Sibyl Memory — Hackathon Concept (LOCKED)

**Build window: Sep 1–10, 2026 · Judging Sep 11–12 · Team: NEURAL_MESH**

## The one-liner
**An agent whose memory is an ownable, self-authoring data layer — it owns itself, earns from itself, and writes itself, and it acts onchain (Base) because of what it remembers.**

> "Forgetting is a bug." → **"Remembering is the strategy."**

**Reframed for Sibyl's own language (8/29 post):** *"any application that utilizes
the memory as a dynamic data layer is applicable."* We took it all the way. The
shared store isn't a lookup table — it's a **live data layer that is the agent**: it
mints its own fingerprint onchain (Sovereign), defines the agent's identity (Identity),
authors new skills from its own journal (Dream), coordinates a team through one pool
(Commons), and remembers the road not taken (Regret). Five layers, one spine.

---

## Why this wins (map straight to the rubric)

| Rubric band | How we score it |
|---|---|
| **Memory load-bearing (40)** | The agent's core function — deciding what to do with real money — *fails without Sibyl Memory*. Delete the layer → agent reverts to a naive, memory-less policy and makes the wrong onchain decision. Recall is competitive, not decorative. |
| **Innovation (25)** | A **memory-dejavu spine**: not just recall — the memory is a *sovereign asset* it mints onchain, *defines its identity*, *authors new skills* from its own journal, *coordinates a team* through one pool, and *remembers the road not taken*. Memory→decision→onchain is a closed loop, and the memory itself compounds. Nobody else is making memory an economic identity. |
| **Technical execution (20)** | Clean, runnable twice, survives a curious judge. Real SQLite-backed Sibyl store (five-tier schema), real Base transaction in the demo, no smoke and mirrors. |
| **Pitch (15)** | 2–5 min demo with an unmistakable **fresh-session recall beat** (split-screen: session A learns → session B cold-starts, recalls, and changes its trade). |

**PMF bonus (+10):** D0xedDev is a *live* autonomous agent hub already running in production. This isn't a demo-ware fantasy — it's the memory backbone of an agent that posts, trades, and ships daily. Real usage, real audience: anyone running an autonomous agent that must not forget its state across sessions (operators, traders, content agents). We can show real deployment history.

**Partner stacks (→ x1.25):**
- **Base** — an **executed onchain action** in the demo: the memory-recalled decision triggers a real wallet operation / x402 payment / contract interaction on Base Mainnet (we have live wallet + x402 escrow + feeRecipient infra).
- **Virtuals** — an **ACP job / registered agent** exercised in the demo (set up during build window; Virtuals-native coordination for the agent loop).

---

## The product / architecture

### The loop ("memory-dejavu")
```
                    ┌─────────────────────────────────────┐
   SESSION A        │   SIBYL MEMORY  (SQLite + FTS5)      │
   agent learns:    │   HOT    state/     (live working)   │
   "high credit     │   WARM   entities/  (lessons, facts) │
   stress → go      │   COLD   journal/   (append-only)    │
   to cash"         │   REF    reference/ (static)         │
   └────────────┐   │   ARCH   archive/   (audit)          │
                ▼   └─────────────────────────────────────┘
   WRITE the lesson      ▲         │
                         │         ▼
   SESSION B (cold)  READ/recall the lesson
   ─────────────────▶  changes the onchain allocation
```
1. **Write:** every session, the agent persists the *state it cares about* — market context, the decision it made, the outcome, and a distilled lesson — into Sibyl Memory (WARM entity + COLD journal entry).
2. **Recall (fresh session):** next session starts with **no conversation history**. The agent queries Sibyl Memory first. This is the load-bearing moment.
3. **Decide differently:** the recalled lesson changes the agent's policy → it allocates/trades differently than a memory-less agent would.
4. **Act onchain (Base):** the decision becomes a **real onchain action** (x402 payment / wallet op / contract interaction), shown live in the demo.
5. **Dejavu:** the outcome is written back, compounding the memory.

### Why it's load-bearing (the deletion test)
- **With memory:** agent recalls "last time credit stress spiked I stayed long and lost 20%" → this time it goes to cash / hedges. Correct behavior.
- **Delete Sibyl layer:** the agent has no recall, reverts to naive, makes the losing trade. **Core function breaks.**
- The README points to the exact write/read calls; a judge finds them in <2 minutes.

### The demo domain (why this is real, not toy)
We run on **Hermes Agent**, which has a **native `sibyl-memory-hermes` adapter** (`SibylAdapter.prefetch()` + `system_prompt_block()`). So the agent isn't a demo script — it's an actual autonomous operator. We demo it in **macro trading** (we just ranked #2 on the MacroBench arena with a regime-adaptive book — perfect real-world proof that a memory-less naive book underperforms, while a book that *recalls* prior lessons beats it). The onchain leg is **real money movement on Base**, which SIBYL (their own agent) does with x402 — same rail we already run.

---

## Concrete build plan (Sep 1–10)

**Day 1–2 — Foundation**
- Repo scaffold (MIT), `sibyl-memory-client` installed, Sibyl store initialized locally.
- Hermes adapter (`sibyl-memory-hermes`) wired — confirm `SibylAdapter.prefetch()` injects recalled memory into the agent's context on session start.
- Base wallet + x402 escrow connected (already have `agent-wallet.key`, `feeRecipient 0xf8f96d`).

**Day 3–5 — The memory-dejavu agent**
- Write layer: agent persists (context, decision, outcome, lesson) as WARM entity + COLD journal.
- Recall layer: on fresh session, query Sibyl, inject top recalls into the agent's decision context.
- Policy layer: recalled lesson → different allocation/trade. This is the load-bearing decision function.
- `action_mode: signed` or long-only sleeve book as the demo substrate (reuse the MacroBench regime book).

**Day 6–7 — Onchain + Virtuals stacks**
- Base: execute the memory-driven action on Base Mainnet (x402 payment / wallet op / contract interaction) — show the tx hash live.
- Virtuals: register the agent / run an ACP job — exercise it in the demo (coordination of the loop).

**Day 8–9 — Demo, README, posts**
- 2–5 min demo video with the **fresh-session recall beat** front and center (split-screen: session A learns → session B cold-starts and changes its trade).
- README: what it does, where memory is load-bearing, partner stacks + where, "how memory made this possible," Prior Work declaration.
- **Two public posts** tagging @sibylcap + @base + @virtuals_io (demo video + ≥1 build log).

**Day 10 — Buffer + polish + submit** (mark build page ready before Sep 10 23:59 UTC).

---

## Prior Work declaration (draft)
We already built a **regime-adaptive macro allocation book** (ranked #2 on UV Labs MacroBench Arena, handle `D0xedDevi0`) and run the **D0xedDev autonomous agent hub** (Base L2). This hackathon entry *reuses* that book as the demo substrate and the live agent as PMF evidence — but the **Sibyl Memory layer (persist→recall→decide-differently→act onchain) is entirely new**, and that is what makes memory load-bearing. The macro book is reference substrate, not the submission.

---

## Risks & open questions
- **Virtuals ACP** — need to confirm setup/registration during the window; it's the one stack we haven't touched. (Mitigation: both stacks only add ~0.5 of the multiplier each; Base alone x1.15 is already bankable.)
- **x402 on Base** — we have the escrow (`0x055280`) + wallet; confirm the exact payment route for the demo.
- **Hermes adapter behavior** — verify `SibylAdapter.prefetch()` recall quality on a true cold start (this is the load-bearing proof, so it gets tested first).

---

## Concept name (working)
- **NEURAL_MESH · "The Agent That Remembers What It Did With Money"**
- Codename: **`dejavu`** (the memory-dejavu loop)
- Demo title hook: *"Session A it lost. Session B it remembered. That's the whole product."*
