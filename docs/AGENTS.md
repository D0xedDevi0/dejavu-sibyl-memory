# AGENTS — drop dejavu into any agent

`dejavu` is a **library first**. One import gives an agent all sixteen memory
layers — no account, no network, no config beyond a file path. This is the
difference between a demo arc and a tool other agents actually adopt.

```bash
pip install -e ".[test]"          # from the repo root
```

## The one import

```python
from dejavu import Memory

m = Memory("agent.db")            # a fresh store. that's it.
```

`Memory` is the whole surface. Every layer is a method on it:

| Layer | Call | What it does |
|---|---|---|
| L9 Discernment | `m.gated_write(cat, name, body, ...)` | persist only what earns its slot |
| L10 Meta | `m.known_unknowns(q)`, `m.confidence(c,n)`, `m.snapshot()` | COVERED/THIN/UNKNOWN, provenance-trusted reliability |
| L11 Guard | `m.guard_book(frame, eq)`, `m.hard_lessons()` | veto a repeat of a recorded loss |
| L12 Exchange | `m.export_lesson(n)`, `m.import_lesson(art)` | verify + gate + buy a foreign lesson |
| L13 Consensus | `m.agent_believe(t, claim)`, `m.reach_consensus(stores, t)` | confidence-weighted cross-agent truth |
| L14 Curriculum | `m.learn_plan({topic: importance})`, `m.gaps_remaining(...)` | schedule what to learn next |
| L15 Distill | `m.distill_rule()`, `m.decide_with_skill(frame)` | scar tissue -> one generalizing rule |
| L16 Consent | `m.wipe_impact()`, `m.request_wipe(force=, reason=)` | refuse / audit a wipe |

Underneath, the five storage tiers (HOT state / WARM entities / COLD journal /
REF reference / ARCH archive) are Sibyl Memory on SQLite + FTS5 — typed,
searchable, no vector DB.

## Pattern 1 — a decision agent (the load-bearing loop)

The canonical shape: **learn from a painful outcome, then the next time the same
shape appears, the memory stops the repeat.**

```python
from dejavu import Memory

m = Memory("agent.db")

# after a bad outcome, write the scar WITH provenance + hard flag
m.write_lesson("crisis", "de-risk when the frame is stressed",
               frame={"vix": 52, "credit_stress": 2.2},
               outcome={"max_drawdown": -0.18})
m.record_provenance("lesson", "crisis", source="backtest",
                    evidence=3, falsifiable=True, hard=True)

# next time a decision is proposed, run it past the memory first
frame = {"vix": 45, "credit_stress": 1.9}
verdict = m.guard_book(frame, proposed_equity=0.55)   # block / warn / allow
if verdict.verdict == "block":
    proposal = de_risk_book(equity=0.05)              # from .policy
```

## Pattern 2 — an autonomous agent that self-improves

```python
m = Memory("agent.db")

# L14: what should I learn next? pass {topic: importance}
plan = m.learn_plan({"credit stress de-risk": 0.9, "alien-trading": 0.9})
for item in plan:
    if item["status"] != "COVERED":
        # acquire it: a paper backtest, a trusted peer's verified lesson...
        m.record_attempt(item["topic"], learned=True, source="backtest")  # bookkeeping
        m.write_lesson(item["topic"], "the invariant I learned")          # real learning
        m.record_provenance("lesson", item["topic"], source="backtest",
                            evidence=2, falsifiable=True)
        # now L10 reports COVERED and the gap drops out of gaps_remaining()
```

## Pattern 3 — a fleet that agrees on the truth

```python
a = Memory("agent-a.db"); b = Memory("agent-b.db")

a.agent_believe("regime", {"regime": "crisis", "equity_target": 0.05},
                provenance={"source": "backtest", "evidence": 3, "hard": True})
b.agent_believe("regime", {"regime": "calm", "equity_target": 0.55})

a.reach_consensus([b], "regime")
# => UNANIMOUS / CONVERGED / MAJORITY / DEADLOCK — never a fabricated winner
```

## Borrowing a lesson (L12 — cross-agent, gated)

```python
seller = Memory("seller.db"); buyer = Memory("buyer.db")
seller.write_lesson("crisis", "de-risk on stress", frame={"vix": 52},
                    outcome={"max_drawdown": -0.18})
seller.record_provenance("lesson", "crisis", source="backtest",
                         evidence=3, hard=True)

artifact = seller.export_lesson("crisis")          # hash + provenance, portable
buyer.import_lesson(artifact, credit_seller=seller) # verifies + L9-gates it
```

## Hard requirements to keep the discipline honest

- **No silent rejection.** Every gate/guard/consensus call returns an explicit
  verdict (`GateDecision`, `GuardVerdict`, status string). Read it.
- **Conflicts are recoverable.** Superseded / evicted / archived memories go to
  ARCH, never deleted. `list_archived()` reads them back.
- **Deadlock is a real answer.** `reach_consensus` returns DEADLOCK on a genuine
  split; it does not fabricate a winner.
- **A wipe is an audited act.** `request_wipe()` refuses without
  `force=True` + `reason`, and journals the deletion to a store-independent log.

## Tests

```bash
pytest tests/ -q          # 124 tests; the second-act suites are offline & fast
pytest tests/test_gates.py tests/test_meta_guard_exchange.py \
       tests/test_consensus_curriculum.py tests/test_distill_consent.py \
       tests/test_spine.py            # the 40 load-bearing L9-L16 + arc tests
```

Full narrative: `docs/doctrine.md` (90s pitch) · `docs/showcase.html` (visual) ·
`docs/judge.md` (proof per claim).
