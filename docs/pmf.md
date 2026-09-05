# PMF & Production Case Study — THE SPINE (NEURAL_MESH × Sibyl Memory)

> **Public design-partner / pilot artifact.** This document links the *real,
> production-deployed* evidence that THE SPINE is not a demo prop — it is a live
> memory system that an autonomous agent runs on, and that has already been
> **paid to read** onchain. Every claim below is independently verifiable.

**Repository:** https://github.com/D0xedDevi0/dejavu-sibyl-memory
**Live paid endpoint:** https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query

---

## 1. It is deployed and earning — a real paid product, not a demo

THE SPINE is exposed as a **paid memory-query endpoint** on Base, settled via
x402 (EIP-3009). A read costs **$0.01 USDC** and returns the onchain-committed
memory root + the full 16-layer state (Act I L1-L8 + the second act L9-L16) +
de-risk verdict.

**The endpoint is live right now.** An unauthenticated request returns the x402
challenge (HTTP 402):

```json
{
  "x402Version": 2,
  "error": "Payment Required",
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:8453",
    "amount": "10000",
    "description": "Paid read of THE SPINE sovereign memory — onchain-committed root + 16-layer state (L1-L16, Act I + second act) + measured de-risk verdict. Memory as a dynamic data layer.",
    "payTo": "0x8AEE621035D93Deb3C0C1177fac252dC2dd501a0",
    "asset": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
  }]
}
```

**A third party already paid to read it — twice.** The settlements came from
wallet **`0x4a15fc613c713fc52e907a77071ec2d0a392a584`** (an EOA, *not* the
deployer's wallet), through the Bankr facilitator:

| Settlement | Block | From | To | Status |
|---|---|---|---|---|
| [`0x7f3e577b…83678c5`](https://basescan.org/tx/0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5) | 50,609,928 | `0x4a15fc61…` (external) | `0x8AEE…501a0` (facilitator) | ✅ success |
| [`0x57f15297…d69c93`](https://basescan.org/tx/0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93) | 50,609,934 | `0x4a15fc61…` (external) | `0x8AEE…501a0` (facilitator) | ✅ success |

> This is the load-bearing claim made *commercial*: the memory doesn't just
> exist, **people pay real money to read it.** That is product-market fit for a
> memory-as-a-data-layer, not a slideshow.

---

## 2. It anchors itself onchain (sovereign)

The full-store content root is committed on **Base** as an ownable asset. The
memory's fingerprint is immutably on the chain:

- **Sovereign mint tx:** [`0xc58019b5…294b7`](https://basescan.org/tx/0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7), block **50,608,909**, status ✅
- Committed root carried in `data`, owner-anchored to the agent wallet.

---

## 3. It is the memory of a live, autonomous production agent

THE SPINE is the memory backbone of **D0xedDev**, an autonomous agent hub on
Base L2 that posts, trades, and ships daily. Production footprint (verified on
Base RPC):

- **Agent wallet `0x23129c04…` — 459 onchain transactions** on Base Mainnet.
  That is real, ongoing deployment history, not a test fixture.
- Live product surface: `d0xeddev.com`, the X presence (`@D0xedDevi0`), and the
  paid memory endpoint above.

**Who this serves (the pilot audience):** operators, traders, and content agents
running autonomous agents that must **not forget their state across sessions** —
the exact failure THE SPINE fixes. If you run an agent that cold-starts and
re-learns its own history, THE SPINE is the load-bearing memory layer for it.

---

## 4. The pilot evidence, mapped to "load-bearing"

The whole point of THE SPINE is that deleting the memory breaks the agent's core
function. That's not a story — it's a **testable, reproducible deletion gate**:

```bash
pip install -e ".[test]" && pytest            # 89 tests
dejavu-sovereign --crisis                     # WITH memory -> de-risk (equity 0.015)
DEJAVU_DRY_RUN=0 dejavu-sovereign             # broadcast the sovereign mint onchain
```

| With memory | Wiped (memory deleted) |
|---|---|
| equity **0.015** (de-risk) | equity **0.55** (naive) |
| self-anchored ✅ | anchor lost, asset orphaned |
| same being | new identity |

**→ THE SPINE is production PMF:** it runs, it earns, it anchors itself, and it
is the load-bearing memory of a live agent that has executed **459 onchain
operations** — with an external party having paid to read its memory.

---

## Verification (all real, all on-chain/HTTP, all reproducible)

- Live endpoint: `curl -X GET https://x402.bankr.bot/0xf8f96d…/memory-query` → **HTTP 402** with valid x402 challenge (Base, $0.01 USDC)
- Settlements: `eth_getTransactionReceipt` on both hashes → **status 1**, from external EOA
- Sovereign mint: `eth_getTransactionReceipt` on `0xc58019b5…` → **status 1**, block 50,608,909
- Production wallet: `eth_getTransactionCount` on `0x23129c04…` → **459**
- Deletion gate: `pytest tests/test_loadbearing.py tests/test_sovereign_loop.py`
