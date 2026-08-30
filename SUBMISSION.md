# Sibyl Memory Hackathon — SUBMISSION

> Canonical submission copy for the September 1–10 build window. Verify every
> public link and timestamp again immediately before marking the build ready.

## Form fields

- **Team name:** NEURAL_MESH
- **Build page slug:** `neural-mesh-eea5`
- **Contact email:** d0xeddev@agentmail.to
- **Repository (public, MIT):** https://github.com/D0xedDevi0/dejavu-sibyl-memory
- **Demo video:** https://github.com/D0xedDevi0/dejavu-sibyl-memory/raw/refs/heads/main/demo/demo_the_spine.mp4 (2:39 canonical final cut)
- **Demo-video post:** https://x.com/D0xedDevi0/status/2093773724596175008
- **Build-log post:** https://x.com/D0xedDevi0/status/2093773782255342027
- **Partner stack claimed now:** Base
- **Virtuals:** implemented/registered integration is documented, but claim the multiplier only if a real ACP job is visibly exercised in the final demo
- **Team size:** 1

## Project tagline

> THE SPINE turns Sibyl Memory into the agent's identity, decision layer,
> coordination commons, evolving skill system, temporal record, sovereign asset,
> and paid data product. Delete it and the agent materially fails.

## Idea / description

Autonomous trading-agent operators lose compounding knowledge every time an
agent cold-starts without durable state. THE SPINE makes Sibyl Memory
load-bearing: Session A records a crisis lesson; a fresh Session B opens the
same Sibyl store with zero conversation history, recalls the lesson, and cuts
equity exposure from 0.55 to 0.05. Delete the store and the same frame falls
back to the naive 0.55 book.

The same store forms a multi-layer dynamic data system: L1 Sovereign commits its
content root on Base; L2 Identity derives the agent identity from that root; L3
Dream converts recurring journal patterns into skills; L4 Commons coordinates
specialist agents through one shared pool; L5 Regret records avoided outcomes;
L6 Temporal tracks belief formation and strategically moves stale knowledge to a
recoverable archive; L7 Sovereign Loop makes the memory self-aware of its own
onchain anchor (it remembers the Base root that committed it); and L8 Conflict
resolves write-time contradictions by superseding the loser to ARCH rather than
overwriting it. A live x402 endpoint sells an onchain-verifiable proof snapshot
for $0.01 USDC, with two successful Base settlement receipts.

Measured deletion gate (seed 1337): capital 0.82 with memory versus 0.49 after
wipe, 1.67× preserved, and mean crisis return −1.65% versus −5.63%.

## Verifiable proof

- **Sovereign root anchor:** https://basescan.org/tx/0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7
- **x402 settlement 1 (0.01 USDC):** https://basescan.org/tx/0x7f3e577bcbfcb7a4611da5e21590bf3377e650c2dc9496f7d4589071d83678c5
- **x402 settlement 2 (0.01 USDC):** https://basescan.org/tx/0x57f15297f37377300ecf742b78d5f90fdb8d2d9d0376a5bb15ca9002ffd69c93
- **Live HTTP 402 endpoint:** https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query
- **PMF / design-partner case study (public):** [`docs/pmf.md`](docs/pmf.md) — links the live paid endpoint, an **external payer** (`0x4a15fc61…`) that settled two real $0.01 USDC reads on Base, the sovereign onchain anchor, and the agent production wallet (459 onchain txs).
- **Executable deletion gate:** `tests/test_loadbearing.py`, `tests/test_spine.py`, `tests/test_spine_ablation.py`, `tests/test_sovereign_loop.py`

## Rubric mapping

| Rubric | Proof |
|---|---|
| Load-bearing 40 | Continuous fresh-session recall/deletion segment plus executable tests: memory → equity 0.05; wipe → 0.55 |
| Innovation 25 | One Sibyl store is identity, sovereign asset, skill author, shared commons, regret record, temporal archive, self-referential onchain anchor, and paid proof layer |
| Technical 20 | Eight-beat canonical arc, deterministic content root, Base receipts, x402 EIP-3009 settlements, reproducible seeded ablation, automated tests |
| Pitch 15 | One THE SPINE narrative, canonical 2–5 minute video, judge proof table, source-linked receipts |
| PMF bonus | ✅ **Claimed.** Public case study [`docs/pmf.md`](docs/pmf.md): live paid endpoint, external payer settled 2× $0.01 USDC reads on Base, sovereign onchain anchor, production agent wallet with 459 txs |

## Prior Work declaration

- **Prior substrate:** MacroBench policy logic and the existing D0xedDev/NEURAL_MESH agent infrastructure.
- **Entry work:** Sibyl persistence/recall, deletion gate, shared-memory fleet, self-learning loop, Sovereign/Identity/Regret/Temporal layers, self-referential onchain anchor, write-time conflict resolution, Base anchoring, x402 paid proof, benchmarks, tests, and submission media.
- Commit history is intentionally preserved. Organizer clarification on pre-window prototyping should be attached if requested.

## Final pre-submit checklist

- [ ] Organizer confirms treatment of work/prototypes created before September 1
- [x] Final demo contains one continuous unedited fresh-session recall segment with on-screen UTC timestamp and commit hash
- [x] `pip install -e ".[test]" && pytest` passes from a clean clone
- [x] GitHub Actions is green on the canonical D0xedDevi0 repository
- [x] Final demo URL opens without authentication and all judge timestamps match
- [x] Repository is public and MIT license is visible
- [x] At least two qualifying public posts are live, tagging `@sibylcap` and the partner actually claimed (`@base`)
- [x] Virtuals was removed from the claimed multiplier because it is not visibly exercised in the final demo
- [x] **One public PMF/design-partner artifact is linked** — [`docs/pmf.md`](docs/pmf.md) (live paid endpoint + external payer settlements + onchain anchor + production wallet)
- [x] Build page `neural-mesh-eea5` was read back and verified after saving
- [x] Marked ready for judging before September 10, 23:59 UTC
