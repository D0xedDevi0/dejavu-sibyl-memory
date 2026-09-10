# THE SPINE — commercial evidence and pilot proposal

**Status: technical payment-rail evidence, not independently established product-market fit.** This replaces the earlier claim that a different transaction sender proved an external paying customer.

## What exists

🟦 A Sibyl-backed deterministic memory/risk prototype with fresh-process deletion tests.
🟦 A [paid snapshot endpoint](https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query) whose source is `demo/x402/memory-query.ts`.
🟦 Historical Base anchor and USDC settlement references, rechecked in [the surface audit](audit-surfaces.md).
🟦 Existing D0xedDev infrastructure as operator context. A wallet's transaction count does not prove usage of this memory product.

The endpoint serves **static snapshot metadata**, not a live read of the local Sibyl database. The constant `asset_resolves=true` is not a runtime verification. Payment success, delivery success, response authenticity and customer independence are distinct claims.

## Settlement references and attribution

[Settlement 1](https://basescan.org/tx/0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5)

[Settlement 2](https://basescan.org/tx/0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93)

Read the USDC `Transfer` logs—not merely transaction `from`—to identify the payer and recipient. A facilitator may submit someone else's signed EIP-3009 authorization. Two transactions do not prove two customers, organic demand, repeat retention, or a design-partner relationship. Receipt status alone does not prove which HTTP response was delivered.

The earlier document equated a relayer-like sender with an external customer and used the phrase “PMF bonus claimed.” That inference is withdrawn. The final audit independently decoded both receipts: `0x23129c0472172d75bed1e6dd061301796760ecd9` paid the facilitator, which forwarded USDC to endpoint owner `0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83`. Both were self-funded. Use the surface audit's decoded transfer evidence for attribution. **No named independent customer, testimonial, or external pilot is established by this report.**

## Buyer and narrow use case

**Buyer:** an operator of restartable autonomous workers making consequential decisions.

**Problem:** after a restart or handoff, an agent loses reviewed incident lessons and repeats a preventable mistake; raw retrieval offers no reliable connection from remembered evidence to an execution constraint.

**Proposed product:** a reviewed memory-to-decision receipt layer. An operator can inspect which lesson constrained a proposal, whether evidence was stale or missing, what guard verdict applied, and whether an action was actually executed.

**First pilot:** one external operator, one worker, one bounded workflow. Start with dry-run risk decisions or operational approvals; do not put live capital behind the demo's deliberate fail-open baseline.

## Pilot acceptance criteria

🟦 Restart persistence: reviewed constraints survive process termination.
🟦 Controlled deletion: the same task changes only when memory is removed.
🟦 Incident recurrence: compare repeated known mistakes with/without memory.
🟦 Guard precision: count correct blocks, false blocks, human overrides and missed hazards.
🟦 Traceability: each decision links evidence IDs and a snapshot digest; execution confirmation remains separate.
🟦 Economics: measure operator time saved and actual paid usage, not wallet activity from unrelated projects.

Report the sample size and failures. Do not convert toy simulated investment returns into a customer ROI claim.

## Next commercial step

Obtain a named operator's consent for a small public pilot artifact: workflow, dates, before/after measurements, limitations and a quote approved by that operator. Until then, pitch this as a technically demonstrated prototype with a credible market hypothesis, **not proven PMF**.
