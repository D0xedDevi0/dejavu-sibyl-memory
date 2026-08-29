# Judge's Cheat-Sheet — THE FLEET (NEURAL_MESH × Sibyl Memory)

> Everything in one page. Each claim → exact file/line, test, tx hash, or video
> timestamp. Reproduce any of it in under two minutes.
>
> **Pitch:** memory as an *ownable, self-authoring data layer*. Five layers, one
> system — the agent doesn't *have* memory, the memory **IS** the agent and owns
> itself, earns from itself, and writes itself. Wipe the store and you don't lose
> a decision, you orphan-destroy a committed onchain asset and turn the agent into
> a different being.

---

## 0. THE SPINE (headline — five layers, one arc)

> **One command, one story:** `dejavu-sovereign --crisis`

| Layer | Proof | Where | Verdict |
|---|---|---|---|
| L1 Sovereign | memory root committed onchain (ownable asset); wipe → **asset orphaned** | `src/dejavu/sovereign.py::sovereign_mint` / `asset_orphaned` | run it |
| L2 Identity | same store = same being; wipe → **new identity** | `src/dejavu/sovereign.py::identity` / `is_same_being` | run it |
| L3 Dream | Learner mines journal → agent accepts a **new skill** it wrote | `src/dejavu/memory.py::learn` · `dejavu-sovereign` L3 line | run it |
| L4 Commons | news/risk → shared board → allocator (multi-agent coordination) | `src/dejavu/fleet.py` | run it |
| L5 Regret | remembers the **road not taken** ("would have lost 18%") | `src/dejavu/regret.py::write_regret` / `recall_regrets` | run it |
| L4 earn | store **earns** — paid query ledger | `src/dejavu/sovereign.py::record_payment` | run it |

```bash
pip install -e ".[test]" && pytest tests/test_sovereign.py tests/test_spine.py -v
# 12 PASSED (root deterministic, identity=memory, mint, orphan-on-wipe, query ledger,
#           write/recall regret, urgency scales, wiped -> zero urgency, full arc)
```

**The economic deletion gate:** with memory → de-risks to 0.015 equity; delete the
store → asset orphaned + new identity + naive 0.55. Memory-load-bearing *with money
attached* — the strongest version of the 40-point proof.

---

## 0. THE FLEET (headline lane — multi-agent shared memory)

**Three agents, one brain. Delete the brain and the team falls apart.**

| Proof | Where | Verdict |
|---|---|---|
| Fleet decision fn (load-bearing) | `src/dejavu/fleet.py` → `fleet_alloc_decide()` — reads the shared board via `read_board()`; **empty board → fails open to naive** (equity 0.55) | read it |
| Specialist agents | `src/dejavu/fleet.py` → `agent_news` / `agent_risk` write `view/news/market` + `view/risk/stress`; `alloc` cold-starts and reads the whole board | read it |
| Executable deletion test | `tests/test_fleet.py` → `test_delete_store_fleet_regresses_to_naive` | run it |
| One-command proof | `dejavu-fleet --crisis` → coordinated de-risk **0.05** · `dejavu-fleet --crisis --wipe` → naive **0.55** (same frame, memory only) | run it |
| Self-evolves (Lane 4) | `dejavu-fleet --crisis --learn` → Learner mines the shared journal, accepts `skill/shape-...` | run it |

```bash
pip install -e ".[test]" && pytest tests/test_fleet.py -v
# 9 PASSED  (board→de-risk, empty-board→naive, delete-store→breaks, learner accepts skill, …)
```

**Why it's load-bearing:** the allocator never calls the other agents — it only reads
memory. Delete the store and there is no coordination signal, so it regresses to the
naive losing book. Multi-agent coordination *through* memory is the innovation (most
submissions are single-agent recall).

---

## 1. The single-agent dejavu loop (fallback lane)

The original memory-dejavu loop — one agent whose past lessons flip its decision.
Deleting Sibyl Memory changes the decision — and loses money.

| Proof | Where | Verdict |
|---|---|---|
| The load-bearing function | `src/dejavu/policy.py` → `decide_differently()` — calls `memory.recall_lessons(...)`; **no recall → fails open to `naive_book()`** (equity 0.55) | read it |
| Read/write layer | `src/dejavu/memory.py` → `recall_lessons` / `write_lesson` / `search` (Sibyl FTS5) | read it |
| Executable deletion test | `tests/test_loadbearing.py` | run it |
| One-command proof | `dejavu --crisis` → de-risks to **0.05** · `dejavu --crisis --wipe` → naive **0.55** (same frame, memory only) | run it |

```bash
pip install -e ".[test]" && pytest tests/test_loadbearing.py -v
# 3 PASSED  (recall→de-risk, fail-open→naive, delete-store→breaks)
```

**Demo beat:** video **1:42–2:07** (`05_sessionB`) — cold start, recalls the lesson,
de-risks, fires a real tx. Contrast gate at **1:19–1:42** (`04_gate`): store wiped →
naive → −18% again.

## 2. It acts onchain (Base stack, executed)

| Proof | Where |
|---|---|
| Live tx (status 1, memory-loaded de-risk) | `0x5175ae5a244b907753cacca9d529c87042ee11332c6e05cf4624d9016d4793dd` · [basescan](https://basescan.org/tx/0x5175ae5a244b907753cacca9d529c87042ee11332c6e05cf4624d9016d4793dd) · block 50108439 |
| Live tx (wallet op) | `0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a` · block 50104833 |
| Code | `src/dejavu/base_action.py` — `eth_account` sign + `eth_sendRawTransaction` |
| Reproduce | `DEJAVU_DRY_RUN=0 dejavu --crisis` (captures hash) |

**Demo beat:** video **1:42–2:07** — on-screen tx hash + block.

## 3. It self-improves (the dejavu loop)

| Proof | Where |
|---|---|
| Learner proposes + agent accepts a skill | `src/dejavu/memory.py` (`Learner`) · `dejavu --learn` → accepts `skill/crisis-derisking` |
| Test | `tests/test_policy.py` (Learner loop) |

**Demo beat:** video **2:38–3:04** (`07_dejavu`) — "recall → consolidate → get sharper."

## 4. Memory is structurally safe

| Proof | Where |
|---|---|
| Compromised/wrong lesson **cannot** force risk | `tests/test_advanced.py::failure_mode_guard` (MacroBench framework owns allocation, not prose) |
| Selective forgetting works | `demo/advanced_analysis.py` #3 — delete one lesson, decision stays de-risked |

**Demo beat:** video **2:07–2:38** (`06_measured`).

## 5. Benchmark-alignment upgrades (Aug 28)

| Upgrade | Proof | Where |
|---|---|---|
| Relational graph (typed edges in Sibyl's native `entity_relations`) | `graph_impact()` two-hop traversal test | `src/dejavu/graph_audit.py` · `tests/test_graph_audit.py::test_graph_impact_two_hops` |
| Scale: 1,000+ record corpus, needle recall top-1 = 100%, 0.1 ms median | `seed_corpus` + `scale_recall_check` | `tests/test_graph_audit.py::test_seed_corpus_scale_and_recall` |
| Tamper-evident journal seal — edit AND delete both break the chain | `seal_journal` / `verify_journal` | `tests/test_graph_audit.py::test_tamper_edit_breaks_chain`, `::test_tamper_delete_breaks_chain` |

## 6. Measured, not marketed

| Metric | No memory | With memory | Reproduce |
|---|---|---|---|
| Mean crisis return (200 frames) | **−9.90%** | **−2.83%** | `pytest tests/test_ablation.py` |
| Loss averted | — | **+7.07pp** | `demo/ablation_figure.png` |
| Decision changed | — | **75%** | `demo/ablation_results.json` |
| Capital after 12 crises | $0.29 | **$0.90** | `demo/advanced_analysis.json` / `growth_curve.png` |

**THE SPINE gate (measured economic deletion):** `demo/spine_ablation.py` (seed 1337):
capital preserved **0.82 vs 0.49 (1.67×)** · mean return −1.65% vs −5.63% · asset
survives + identity stable WITH memory; **identity churns to a new being on wipe**.
`demo/spine_gate_figure.png` · `tests/test_spine_ablation.py`.

All seeds fixed (1337), honest numbers — no fabricated judge output.

## 6. LongMemEval resonance (credibility — same suite Sibyl ranks on)

The retrieval engine behind the hub (**NEURAL_MESH resonance**) benchmarks on the
same **100-case LongMemEval suite** the Sibyl team itself uses. LLM-judge-graded
semantic recall: **resonance > dense** (EM 0.25 vs 0.20 · F1 0.344 vs 0.326),
strongest on `single-session-user` (MRR 0.68, judge F1 0.73). Full breakouts in
`docs/longmemeval.md` / `../NEURAL_MESH/bench/longmemeval_harness.py`.

## 7. PMF bonus

`dejavu` is the memory backbone of **D0xedDev**, a live autonomous agent hub on
Base (d0xeddev.com) — real production usage, real audience, real deployment
history. Not a toy. **Demo beat:** video **3:04–3:28** (`08_pmf`).

---

## 30-second summary for the judge

> **THE FLEET**: three specialist agents — news, risk, allocator — coordinate through
> one shared Sibyl store. The allocator never calls the others; it reads memory alone,
> so deleting the store collapses the team back to a naive losing book — that's the
> 40-point proof, upgraded to multi-agent. It self-evolves (Learner accepts skills),
> fires real Base txs, and every number is measured. The single-agent `dejavu` loop is
> the documented fallback. MIT.
