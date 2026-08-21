# Judge's Cheat-Sheet — dejavu (NEURAL_MESH × Sibyl Memory)

> Everything in one page. Each claim → exact file/line, test, tx hash, or video
> timestamp. Reproduce any of it in under two minutes.
>
> **Pitch:** a self-improving autonomous agent whose **onchain (Base) decisions are
> driven by its own persistent Sibyl Memory**. Forgetting is a bug. Remembering is
> the strategy.

---

## 1. The core claim (40-pt load-bearing gate)

**Deleting Sibyl Memory changes the decision — and loses money.**

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

## 5. Measured, not marketed

| Metric | No memory | With memory | Reproduce |
|---|---|---|---|
| Mean crisis return (200 frames) | **−9.90%** | **−2.83%** | `pytest tests/test_ablation.py` |
| Loss averted | — | **+7.07pp** | `demo/ablation_figure.png` |
| Decision changed | — | **75%** | `demo/ablation_results.json` |
| Capital after 12 crises | $0.29 | **$0.90** | `demo/advanced_analysis.json` / `growth_curve.png` |

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

> It remembered, so it de-risked, and that decision **fired a real Base tx**.
> Delete the store and it loses again — that's the 40-point proof. It compounds
> (self-learns skills), it's structurally safe against compromised lessons, and
> every number is measured and reproducible. This is the live memory backbone of
> D0xedDev. MIT.
