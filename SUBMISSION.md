# Sibyl Memory Hackathon — SUBMISSION (draft, ready to file Sep 1–10)

> Fill + submit during the build window. Everything below is final copy —
> paste straight into the form / build page. Verified 2026-08-28 (bench-alignment upgrades + demo v3 included).

## Form fields

- **Team name:** NEURAL_MESH
- **Build page slug:** neural-mesh-eea5
- **Contact email:** d0xeddev@agentmail.to
- **Repo (public, MIT):** https://github.com/D0xedDevi0/dejavu-sibyl-memory
- **Demo video (submission artifact):** https://github.com/D0xedDevi0/dejavu-sibyl-memory/blob/main/demo/demo_video_v2.mp4
  (4:42, narrated; fresh-session recall beat at ~0:45 — allocator cold-starts on an empty store; graph/scale ~2:30, audit chain ~3:05)
- **Partner stacks:** Base · Virtuals Protocol (x1.25 multiplier)
- **Team size:** 1

## Project tagline (one-liner)

> THE FLEET — memory as a **dynamic data layer**: a team of specialist agents
> coordinated by ONE shared Sibyl Memory store. Delete the memory and the team
> falls apart.

## Idea / description (form "idea" field)

Not one agent that remembers — a TEAM that remembers. News and risk agents
write their views of the world to a single shared Sibyl Memory store; the
allocator agent cold-starts with zero context and reads only that board to
coordinate a de-risk decision that fires as a real Base transaction. The
load-bearing proof is executable: delete the shared store and the allocator
reads an empty board, fails open to naive overweight equity, and loses the
same money again (`pytest tests/test_fleet.py`). The fleet also self-evolves:
a Learner mines its own shared journal and proposes skills the team accepts.
58 tests green, real Base txs verified on mainnet, typed relational graph in Sibyl's native entity_relations, 1,385-record scale stress with 100% top-1 needle recall at 0.1 ms, and a tamper-evident SHA-256 audit chain over the journal — every number measured
(seed 1337). Single-agent `dejavu` loop included as documented fallback lane.

## Rubric mapping (judge cheat-sheet: docs/judge.md)

| Rubric | Our proof |
|---|---|
| Load-bearing 40 | `tests/test_fleet.py` deletion gate — empty board → naive 0.55 vs coordinated 0.05 |
| Innovation 25 | multi-agent coordination *through* memory (no agent-to-agent calls) + Lane 4 self-evolution |
| Technical 20 | 58 tests, typed facade over real SDK, tenant-correct Learner wiring, native entity_relations graph, 0.1 ms scale recall, tamper-evident audit chain |
| Pitch 15 | 4:42 narrated video (11 scenes incl. graph/scale + audit), judge cheat-sheet, reproducible builder checked in |
| PMF bonus +10 | D0xedDev production hub on Base; Virtuals ACP agent registered |

## Pre-submit checklist (do these Sep 1–10)

- [ ] Re-run `pip install -e ".[test]" && pytest` → 58 passed
- [ ] Re-run `.venv/bin/python -m dejavu-fleet --crisis --learn` → live proof output
- [ ] Confirm repo public + MIT license visible
- [ ] Upload/attach fleet_video.mp4 wherever the form wants media
- [ ] Post 2 public posts tagging @sibylcap + @base + @virtuals_io
      (3 already drafted in demo/post-0*.md — refresh dates before posting)
- [ ] Verify build page shows updated links (D0xedDevi0 canonical)

## Registration re-run (if ever needed) — Playwright Python

Next.js server action; MUST wait for React hydration (wait_until="load" + ~2.5s)
before filling+clicking, else "session expired." Chromium at
/opt/data/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome via
/opt/data/.venv-pw/bin/python. Fields: team, email, size, partnerStacks
(Base / "Virtuals Protocol"), idea. Submit = form button[type=submit].
