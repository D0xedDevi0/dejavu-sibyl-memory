# echo — The Agent That Remembers What It Did With Money

**NEURAL_MESH × Sibyl Memory** · Sibyl Memory Hackathon (hack.sibyllabs.org)

> *"Forgetting is a bug. Remembering is the strategy."*

A self-improving autonomous agent whose onchain (Base) decisions are **driven by its
own persistent memory**. Codename `echo` — the memory-echo loop.

---

## What it does

An agent manages a macro capital book. In **Session A** it faces a stressed market,
stays overweight equity (naive), takes a ~-18% drawdown, and writes a distilled
lesson into its **Sibyl Memory** store. A fresh process (**Session B**) cold-starts
with zero conversation history, **queries Sibyl first**, recalls that lesson, and
**decides differently** — de-risking into cash/rates/hedges. That decision then
triggers a **real onchain action on Base**.

```
SESSION A ──learn──► SIBYL MEMORY (SQLite + FTS5) ──recall──► SESSION B decides
   write lesson       five tiers: HOT/WARM/COLD/REF/ARCH    changes the book
        ▲                                                         │
        └──────────── echo: outcome written back, compounds ◄────┘
                                                          │
                                                          ▼
                                            ⛓ BASE ONCHAIN ACTION (wallet op)
```

## Where Sibyl Memory is load-bearing (exact file/line)

Sibyl Memory is **not** decorative — the core decision function *fails without it*.

- **`src/echo/policy.py:decide_differently`** — the load-bearing function. It calls
  `memory.recall_lessons(...)` (→ `src/echo/memory.py:recall_lessons`, an FTS5
  `search` on the store). If no lesson is recalled, it **fails open to
  `naive_book()`** (overweight equity).
- **`src/echo/memory.py:recall_lessons` / `write_lesson` / `search`** — the read/write
  that persist and retrieve the lesson across sessions.

**The deletion test** (the judge's check, executable): `tests/test_loadbearing.py`.
Delete the store → no recall → the agent reverts to naive and makes the losing call.

```
$ pytest tests/test_loadbearing.py -v
test_with_memory_recalls_and_de_risks ..... PASSED   # equity → 0.05
test_without_memory_fails_open_to_naive ... PASSED   # equity → 0.55
test_deleting_store_between_sessions_breaks_behavior PASSED
```

Run it yourself in one command (see **Run** below): `echo --crisis` recalls and
de-risks to 0.05; `echo --crisis --wipe` (deleted store) stays naive at 0.55. Same
frame, different decision — **because of memory**.

## Partner stacks used + where

| Stack | Where | What we do |
|---|---|---|
| **Base** | `src/echo/base_action.py` | A memory-driven decision executes a **real Base Mainnet wallet operation** (`eth_account` sign + `eth_sendRawTransaction`). Live verified tx below. |
| **Virtuals Protocol** | `src/echo/virtuals.py`, `virtuals-echo-agent.md` | The loop is coordinated by a **registered, signer-enabled Virtuals ACP agent** named `echo` (EVM wallet `0xef25e214...47bb`, ACP_ONLY signer policy — it can transact onchain autonomously). Run with `echo --virtuals`.

**Executed Base transaction (verified onchain, status 1):**
[`0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a`](https://basescan.org/tx/0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a)
— block 50104833, from/to agent wallet `0x23129c0472172D75bEd1e6dd061301796760Ecd9`.

## How memory made this possible

Without Sibyl Memory there is no cross-session state: every run is a cold start that
makes the same naive mistake. Memory is what lets the agent **compound** — it
recalls its own past outcomes, changes policy, and writes the new result back
(memory-echo loop). The agent literally gets smarter the more it runs. And because
the decision is memory-driven, the resulting action *onchain is memory-driven too*.

## Prior Work declaration

- **Substrate:** the MacroBench regime-adaptive macro book (ranked **#2** on the UV
  Labs MacroBench Arena, handle `D0xedDevi0`). Reused here as the policy substrate
  (`src/echo/policy.py`).
- **PMF evidence:** D0xedDev, a live autonomous agent hub on Base (`d0xeddev.com`).
- **New in this entry (the submission):** the Sibyl Memory layer — persist → recall
  → decide-differently → act onchain, and the memory-echo loop that closes it.
  The macro book is reference substrate, not the submission.

## Run

```bash
pip install -e ".[test]" && pytest            # 22 tests incl. the deletion gate
echo --crisis                                  # with memory  -> de-risk (equity 0.05)
echo --crisis --wipe                           # store deleted -> naive  (equity 0.55)
ECHO_DRY_RUN=0 echo --crisis                   # fire a REAL Base tx (captures hash)
echo --crisis --learn --virtuals               # full loop: recall + self-learn + ACP coordinate
```

Deps: `sibyl-memory-client`, `sibyl-memory-cli`, `sibyl-memory-hermes` (local,
headless, no account/network). Onchain: `eth_account`, `web3`. Virtuals: the
registered `echo` agent via the acp-cli (see `virtuals-echo-agent.md` for the
`TS_KEYRING_BACKEND=file` requirement).

## License

MIT
