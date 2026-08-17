# NEURAL_MESH × Sibyl Memory — BUILD SPEC (goals, architecture, exact steps)

**Hackathon:** Sibyl Memory Hackathon · hack.sibyllabs.org
**Team:** NEURAL_MESH · slug `neural-mesh-eea5`
**Build window:** Sep 1–10, 2026 (all UTC) · Submit ≤ Sep 10 23:59 UTC
**Repos/docs:** CONCEPT.md (vision) · this file (executable spec)

> THIS IS THE SOURCE OF TRUTH FOR THE BUILD. A fresh agent session must be able
> to pick this up cold and execute the roadmap with zero backstory. Everything
> verified against the real SDK is marked **[VERIFIED]**. Everything that still
> needs hands-on work is marked **[TODO]** with the exact next action.

---

## 0. The pitch (memorize this)

**A self-improving autonomous agent whose decisions are *driven by* its own
persistent memory — and it acts onchain (Base) because of what it remembers.**

- "Forgetting is a bug" → **"Remembering is the strategy."**
- Demo hook: *"Session A it lost. Session B it remembered. That's the whole product."*
- Codename: **`echo`** (the memory-echo loop)

### Scoring (target: win top-5, aim #1)
`Builder Score = (Judge Score + PMF bonus) × Stack multiplier`

| Band | Points | How we win |
|---|---|---|
| Memory load-bearing | 40 | **Core decision function fails without Sibyl Memory.** Delete store → naive → losing trade. [VERIFIED in prototype] |
| Innovation | 25 | Memory-echo loop: agent writes its own outcomes back and compounds (self-learning). Memory→decision→onchain closed loop. |
| Technical | 20 | Clean, runnable twice, SQLite-backed Sibyl store, real Base tx in demo, no smoke & mirrors. |
| Pitch | 15 | 2–5 min demo with unmistakable fresh-session recall beat. |
| PMF bonus | +10 | D0xedDev is a live production agent hub — real usage, real audience, deployment history. |
| Stacks | x1.25 | Base (executed onchain action) + Virtuals (ACP job/agent), both exercised in demo. Sibyl Memory mandatory, never counts as a stack. |

---

## 1. Architecture — the memory-echo loop

```
                 ┌──────────────────────────────────────────┐
 SESSION A       │   SIBYL MEMORY  (SQLite + FTS5, file-based)│
 agent decides   │   HOT   state/       live working state    │
 + learns lesson │   WARM  entities/    facts, lessons (SSOT) │
 └─────────────► │   COLD  journal/     append-only audit     │
    WRITE        │   REF   reference/   static knowledge      │
                 │   ARCH  archive/     retired entities      │
                 └──────────────────────────────────────────┘
                        ▲                     │
                        │                     ▼  READ/RECALL on cold start
                   WRITE outcome           changes the decision
                        │                     │
                        └────── echo: outcome written back, compounds ──┘
                                │
                                ▼
                    ⛓️ BASE ONCHAIN ACTION (x402 payment / wallet op)
                    🤖 VIRTUALs ACP job coordinates the loop
```

### The 5 steps (each is a named module in the repo)
1. **write** — persist (market context, decision, outcome, distilled lesson)
2. **recall** — fresh session starts w/ no chat history; query Sibyl first
3. **decide_differently** — recalled lesson changes policy (the load-bearing fn)
4. **act_onchain** — decision becomes a real Base transaction (x402 / wallet op)
5. **echo** — outcome written back; memory compounds

### Deletion test (the judge's check)
- **With memory:** recalls "credit_stress>0.7 → de-risk" → goes to cash/rates. Correct.
- **Delete Sibyl layer:** no recall → naive (stays long equity) → loses 18%+. **Breaks.**
- README points to the exact write/read calls; judge finds them in <2 min.

---

## 2. Environment — verified working stack [VERIFIED]

**Python venv:** `/opt/data/sibyl-hackathon/.venv` (python3.13)
**Packages installed:**
- `sibyl-memory-client==0.6.1` [VERIFIED]
- `sibyl-memory-cli` [VERIFIED, CLI binary `sibyl` works]
- `sibyl-memory-hermes` [VERIFIED, adapter imports]

**Key API facts (all [VERIFIED] by direct execution):**
```python
from sibyl_memory_client import MemoryClient, Storage, Learner
# Local, headless, NO account / NO network required:
c = MemoryClient.local("/path/to/memory.db")   # tenant defaults to all-zeros UUID
st = c.storage                                  # Storage (a PROPERTY, not a method!)

# Entity (WARM / single-source-of-truth per (category,name)):
c.set_entity("lesson","crisis-derisking",{...}, status="active")
c.get_entity("lesson","crisis-derisking")       # -> dict | raises NotFoundError
c.list_entities(category=None, status=None, limit=100)
c.search("credit stress", limit=20)             # FTS5, returns list of dicts w/ 'tier','key','body'

# Journal (COLD / append-only):
c.write_event(evaluated={...}, acted={...}, forward=..., extra={...})  # -> event id
c.read_events(limit=50, since=None, until=None)

# Reference / State (REFERENCE / HOT):
c.set_reference(key, body, metadata=None)
c.get_reference(key)
c.set_state(key, body); c.get_state(key)

# Learner (self-learning / skill proposals):
lrn = Learner(st)                               # NOTE: pass st (Storage), NOT c.storage()
report = lrn.run()                              # signature: run(*, since=None) -> LearningRunReport
# Learner.list_proposals() / accept_proposal(proposal_id, note=) / reject_proposal(...)

# Hermes adapter:
from sibyl_memory_hermes import SibylMemoryProvider
prov = SibylMemoryProvider(db_path="/path/memory.db", require_credentials=False)
prov.health()                                   # -> {'ok':True,'schema_version':4,...}
prov.remember(category,name,body,status=None)
prov.recall(category,name)
prov.search(query, limit=20)
prov.save_context(inputs={...}, outputs={...})  # journal entry, returns id
prov.load_context(limit=20)
prov.list(category=None, status=None, limit=100)
prov.forget(category,name)
```

**Pitfalls discovered [VERIFIED]:**
- `MemoryClient.storage` is a **property**, not a method → use `c.storage` not `c.storage()`.
- `Learner.run()` takes **no `limit` kwarg** → use `run(since=...)`; set cap via `Learner(storage, max_proposals_per_run=N)`.
- `sibyl-memory-hermes.provider` is a **module**, not a callable. Construct `SibylMemoryProvider(...)` directly.
- The CLI `sibyl init` opens a browser auth flow (not needed for local SDK use). Use the SDK or `require_credentials=False` adapter for headless work.
- Search default = **AND-of-tokens**; wrap multi-word query in double quotes for phrase mode (client 0.4.2+ behavior). This matters for recall quality — test both.

---

## 3. Repo layout (goal)

```
/opt/data/sibyl-hackathon/
├── CONCEPT.md            # vision + scoring map (done)
├── BUILD_SPEC.md         # THIS FILE
├── registration.md       # creds + build link (done)
├── proto/
│   └── echo_loop.py      # [DONE] load-bearing prototype (works)
├── src/echo/             # THE REAL BUILD
│   ├── __init__.py
│   ├── memory.py         # Sibyl wrapper (write/recall/search)
│   ├── policy.py         # decide_differently (load-bearing decision fn)
│   ├── base_action.py    # onchain leg (x402 / wallet op)
│   ├── agent.py          # orchestration loop (session A/B)
│   └── config.py
├── tests/
│   ├── test_loadbearing.py   # deletion test (CI gate)
│   ├── test_recall.py
│   └── test_policy.py
├── demo/                 # 2-5min demo script + video
├── README.md             # submission README (see §8)
└── pyproject.toml        # MIT, deps pinned
```

---

## 4. Milestone roadmap (Sep 1–10)

### M1 — Foundation (Day 1–2)
- [x] Repo scaffold [DONE: venv + proto]
- [x] `pyproject.toml`, package layout `src/echo/` [DONE, commit 0c9d01b]
- [x] `memory.py` wrapper: `MemoryClient.local` + all 5-tier ops, typed [DONE]
- [x] `base_action.py` onchain stub (dry-run, M3 wires real tx) [DONE]
- [x] Pytest setup; `test_loadbearing.py` (the deletion gate) green from day 1 [DONE: 12 tests pass]
- [x] Git repo initialized, `.gitignore` excludes `.venv/`/`data/`/`*.db` [DONE]

### M2 — The memory-echo agent (Day 3–5)
- [x] `policy.py`: reuse the **MacroBench regime book** as substrate
      (ranked #2, handle `D0xedDevi0`) — recalled lesson flips allocation
      [DONE: risk_score/RISK_ON/RISK_OFF/macrobench_sleeves ported from
       /opt/data/uvlabs-arena/agent.py; decide_differently returns the real
       defensive book on recall; tests pin the substrate]
- [ ] `agent.py`: `run_session(frame)` → write → (fresh proc) → recall → decide
      [PARTIAL: run_sessions() + `echo` CLI work; wire MacroBench frame]
- [ ] Learner integration: journal patterns → skill proposals the agent accepts
      [PARTIAL: Memory.learner + learn()/accept_proposal() exposed; test confirms pipeline]
- [x] `test_recall.py` + `test_policy.py` green [DONE: 14 total pass]

### M3 — Base onchain leg (Day 6–7)
- [x] `base_action.py`: x402 payment OR wallet op using:
      - RPC `mainnet.base.org` [VERIFIED live, chainId 0x2105/8453]
      - key `/opt/data/.secrets/agent-wallet.key` [EXISTS: 0x23129c0472172D75bEd1e6dd061301796760Ecd9, ~5e-05 ETH, 409 prior txs]
      - x402 Escrow `0x055280...` · feeRecipient `0xf8f96d` [MEMORY; NOTE: feeRecipient is a short/placeholder form, not a valid address — execute() falls back to self-transfer]
- [x] memory-driven decision → real Base tx (wallet-op route wired: eth_account signs + eth_sendRawTransaction; dry_run default); tx hash captured for demo [DONE, code+tests; live broadcast not yet fired]
- [x] confirm exact x402 payment route (quoteOnlyFees feeRecipient pattern) [DONE: wallet-op chosen as the robust demo proof; x402/EIP-3009 needs a funded USDC wallet — see §10]
- [ ] FIRE a real Base tx and capture the hash (during demo, or on request) [PENDING: needs ECHO_DRY_RUN=0]
- [ ] Virtuals ACP (see M4)

### M4 — Virtuals ACP (Day 7–8)
- [ ] Register agent / run ACP job on Virtuals Protocol
- [ ] Exercise it in the loop (coordination) in the demo
- [ ] NOTE: this is the ONE stack not yet touched. First task in the window is
      reconnaissance on Virtuals ACP setup. Both-stack x1.25 is the target;
      Base alone x1.15 is already bankable.

### M5 — Demo + README + posts (Day 8–9)
- [ ] 2–5 min demo video, fresh-session recall beat front-and-center
      (split-screen: session A learns → session B cold-starts and changes trade)
- [ ] README per §8
- [ ] **Two public posts** tagging @sibylcap + @base + @virtuals (≥1 build log + demo)
- [ ] Prior Work declaration (MacroBench book = substrate, not the submission)

### M6 — Buffer + submit (Day 10)
- [ ] Polish, re-run all tests, mark build page ready
- [ ] Submit ≤ Sep 10 23:59 UTC (must be public repo MIT/Apache-2.0)

---

## 5. The load-bearing decision function (core algorithm)

```python
def decide(frame, memory) -> book:
    """THE function. Fails open to naive without memory."""
    crisis_lessons = recall_lessons(memory, "credit stress crisis drawdown")
    cs, vix = frame["credit_stress"], frame["vix"]
    if (cs > 0.7 or vix > 30) and crisis_lessons:
        return de_risk_book()        # equity→0.05, cash/rates/hedges↑
    return naive_book()              # equity→0.55 ← what happens w/o memory
```
- `recall_lessons` wraps `memory.search(...)` + filters `body["lesson"]`.
- **The deletion gate** = `if not memory: return naive_book()` (i.e., delete store,
  no recall → naive). This is the 40-point proof.
- Prototype `proto/echo_loop.py` already implements exactly this and passes. [VERIFIED]

---

## 6. Demo script (2–5 min) — the money shot

1. **Cold open (0:00–0:20):** "Forgetting is a bug. Here's an agent that
   remembered what it did with real money."
2. **Session A (0:20–1:00):** agent faces a market frame, naive → stays long,
   credit stress spikes → -18% drawdown. It writes the lesson to Sibyl Memory.
3. **Deletion contrast (1:00–1:30):** show `ls memory.db`; wipe it; fresh session B
   → naive again → same loss. *"That's what forgetting costs."*
4. **With memory (1:30–2:30):** fresh cold-start session B recalls the lesson →
   de-risks → survives. Show the search hit returning the lesson.
5. **Onchain (2:30–3:30):** memory-driven decision executes a REAL Base tx
   (x402 / wallet op) — show tx hash + explorer. *"It didn't just remember. It acted."*
6. **Echo/compounding (3:30–4:30):** show the Learner proposing a skill from the
   journal. *"Session A it lost. Session B it remembered. That's the whole product."*
7. **PMF (4:30–5:00):** "This is the memory backbone of D0xedDev, a live
   autonomous agent hub on Base that's been running since [date]."

---

## 7. Partner stacks — exact requirements [from rules]

- **Base:** "an executed onchain action: a wallet operation, an x402 payment, a
  B20 read, or a contract interaction shown in the demo." → We do **x402 payment
  or wallet op**, tx hash visible.
- **Virtuals:** "an ACP job, a registered or transacting agent, or another
  Virtuals-native integration exercised in the demo." → We register/run an **ACP
  job** coordinating the loop.
- **Multiplier:** 0 stacks = x1.0 · 1 = x1.15 · 2 = x1.25. Sibyl Memory is
  mandatory and **never counts** as a stack.

---

## 8. README requirements (submission gate) [from rules]
- What it does
- Where Sibyl Memory is load-bearing (exact file/line)
- Partner stacks used + where
- How memory made this possible
- Prior Work declaration
- Run instructions (one command)

---

## 9. Submission checklist (final)
- [ ] Public repo, MIT or Apache-2.0 license
- [ ] 2–5 min demo video with fresh-session recall beat
- [ ] README complete (all §8 sections)
- [ ] Two public posts (tag @sibylcap + @base + @virtuals), links in submission
- [ ] Build page marked ready on hack.sibyllabs.org (slug neural-mesh-eea5)
- [ ] Prior Work declared (MacroBench book + D0xedDev are substrate/evidence)

---

## 10. Risks & open questions
| Risk | Mitigation |
|---|---|
| Virtuals ACP unfamiliar | Recon first task of window; Base x1.15 is floor if Virtuals fails |
| x402 exact route | escrow 0x055280 + wallet exist; wallet-op chosen as robust demo proof (real Base tx, no EIP-3009 dependency). x402 needs funded USDC wallet → optional upgrade. feeRecipient `0xf8f96d` is short-form/placeholder, not a valid address — resolve to full address or rely on self-transfer. |
| Hermes adapter cold-start recall quality | Test `SibylAdapter.prefetch()` on a true empty context; search default is AND-tokens — phrase-quote multi-word queries |
| Judge can't find load-bearing code | README points to exact file/line; `test_loadbearing.py` is the proof |
| Build window tight | Prototype already done; most heavy lifting (M1–M2) is porting proven logic |

---

## 11. Immediate next actions (this session or first build session)
1. **[DONE 2026-08-17]** Port `proto/echo_loop.py` → `src/echo/{memory,policy,agent,base_action,config}.py`; `tests/` (12 green); git init commit `0c9d01b`.
2. **[DONE 2026-08-17]** Draft + post the "we signed up" build-in-public post (see §12). — NOTE: the companion draft post from the prior session was NOT found in this repo; draft fresh if not yet posted.
3. **[DONE 2026-08-17]** Wire the **MacroBench regime book** into `policy.decide_differently` (risk_score/RISK_ON/RISK_OFF/macrobench_sleeves ported from `/opt/data/uvlabs-arena/agent.py`; recall now returns the real defensive book; 14 tests green).
4. **[DONE 2026-08-17]** Base onchain leg: wired real wallet-op broadcast (eth_account sign + eth_sendRawTransaction, dry_run default) into `base_action.execute`; verified RPC/wallet/chainId live; 18 tests green. Live fire pending (`ECHO_DRY_RUN=0`).
5. **[NEXT]** Learner self-learning loop: journal → skill proposals → accept (pipeline wired, tune).
6. **[WINDOW]** Virtuals ACP recon (first task of build window; Base x1.15 is the bankable floor).
7. **[WINDOW]** Demo video, README, 2nd post, submit ≤ Sep 10 23:59 UTC.

---

## 12. Build-in-public post #1 (signed-up announcement) — DRAFTED SEPARATELY
See the companion X post in this conversation; bank it now to satisfy the
2-post requirement early. Tag @sibylcap + @base + @virtuals. Devio voice:
🟦 bullets, high energy, thesis-style, NFA/DYOR not needed here (not a token
shill — it's a dev announcement, keep it hype but honest).
