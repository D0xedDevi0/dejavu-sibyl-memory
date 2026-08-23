# THE FLEET — memory-deepening upgrades (researched 2026-08-23)

Fusion of (a) full audit of the vendored `sibyl_memory_client` SDK surface vs
what our code actually calls, and (b) state-of-the-art agentic-memory research
(MemGPT/Letta, Generative Agents, Reflexion, Voyager, A-MEM, Mem0, Zep/Graphiti,
HippoRAG, MemoryBank, CoALA, sleep-time-consolidation work).

## Gap map: SDK features we DON'T use yet

| SDK capability | Where | Our use |
|---|---|---|
| `multi_record_search()` — two-stage retrieve-then-verify w/ IDF-style df weighting + abstention on unsatisfiable queries | `multi_record.py` | never |
| Shadow trigram index — substring/CJK/fuzzy zero-hit fallback across ALL tiers | `shadow.py` | passive only |
| `Linter` — store health findings (critical/warning/info) | `lint.py` | never |
| `archive_entity()` + ARCH tier lifecycle | `client.py` | never |
| `BYOKSummarizer` — plug an LLM into Learner skill synthesis | `learning.py` | deterministic summarizer only |
| Cap/tier gates (`free_tier_status`, `CapGate`) | `_capcheck.py` | unused |
| REFERENCE-tier metadata payloads | `set_reference(metadata=)` | bare |

## What SOTA says counts as deep (and our current equivalent)

- **Mem0 four-op writes** (ADD/UPDATE/DELETE/NOOP) = write-time conflict
  resolution. Ours: blind overwrite via `set_entity`. GAP.
- **Mem0 Memory Decay** = search-time re-rank by access recency (Bjork
  retrieval-strength vs storage-strength). Ours: none. GAP.
- **Zep/Graphiti temporal KG** = valid-interval edge validity. Ours: journal ts
  only, no supersession chains. PARTIAL.
- **Sleep-time consolidation** (Letta) = offline merge/dedup passes. Ours:
  none between episodes. GAP.
- **Voyager skill library** = skills mined from experience → we HAVE this via
  the Learner. Table stakes covered ✓.
- **Reflexion** = verbal self-critique persisted across trials → our lessons ≈
  this ✓ but not outcome-driven automatically.
- **Blackboard architectures** (classic Hayes-Roth; our whole pitch) ✓ — few
  modern systems do memory-mediated multi-agent coordination. This is our
  innovation moat; deepen it.

## Ranked upgrade backlog (impact × feasibility)

1. **Write-time conflict resolution ("supersession")** — when news/risk write a
   view that contradicts the existing one, don't blind-overwrite: journal a
   SUPERSEDES event linking old→new, keep the loser in ARCH via
   `archive_entity()`. Mem0-equivalent, uses real SDK tiers, strengthens both
   load-bearing story and audit trail. ~1 day.
2. **Retrieval-strength decay** — track per-view access/recency in REFERENCE
   metadata; allocator's board read re-ranks views by a decay score (1.5x fresh
   → 0.3x stale). Direct Mem0-Decay analog, cheap, very demoable. ~0.5 day.
3. **Consolidation pass ("fleet sleep")** — offline pass between episodes:
   dedupe near-identical views, merge repeated lessons, lint the store with the
   SDK `Linter`, promote HOT→WARM→ARCH per policy. Sleep-time-compute story.
   ~1 day.
4. **LLM-powered skill synthesis** — wire `BYOKSummarizer` to our Nous free
   model so accepted fleet skills are actual synthesized strategies, not
   template text. Big quality jump in the Lane 4 beat. ~0.5 day.
5. **Verify-gated board reads** — swap allocator's `list_entities` board read
   for `multi_record_search` when querying past decisions/lessons: IDF-weighted,
   abstains instead of hallucinating a match ("the memory knows what it does
   NOT know"). ~0.5 day.
6. **Temporal board** — each view carries `valid_from/valid_to`; allocator can
   reconstruct "what did the board look like at episode N" (Graphiti-lite).
   Enables a killer demo beat: replay history through the store. ~1.5 days.
7. **Memory health gate in CI** — run SDK `Linter` in tests; critical findings
   fail the build. Cheap technical-points polish. ~2h.

## Non-goals

Vector embeddings (SDK is lexical; judges care about load-bearing + novelty,
not ANN), cross-tenant reads (not exposed by design), external graph DBs
(defeats "one shared store" simplicity).
