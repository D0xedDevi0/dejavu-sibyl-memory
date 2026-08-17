# Sibyl Memory Hackathon — Team Registration (confirmed 2026-08-17)

- Team name: NEURAL_MESH
- Build page slug: neural-mesh-eea5
- Build link: https://hack.sibyllabs.org/team/enter?slug=neural-mesh-eea5&token=d103701110ba9d532e01ba0e3e403936a3272cbe80ebc499
- Contact email: basednukem@gmail.com
- Team size: 1
- Partner stacks declared: Base, Virtuals Protocol  (x1.25 multiplier target)
- Timeline: Registration open Aug 16-31 · Build window Sep 1-10 · Workshops Sep 5-7 · Judging Sep 11-12 · Winners Sep 13-15 (all UTC)
- Prizes: $10k USDC top-5; 1st = $4k + Network School residency; 2nd = $2.5k + Base Support Program entry
- Scoring: Builder Score = (Judge Score + PMF bonus) x Stack multiplier
  - Gate: Sibyl Memory must be LOAD-BEARING (delete it → core function breaks)
  - Rubric: memory load-bearing 40, innovation 25, technical 20, pitch 15, PMF bonus +10
  - Stacks: 0=x1.0, 1=x1.15, 2=x1.25 (Sibyl Memory mandatory, never counts as stack)
- Submit: public repo (MIT/Apache-2.0), 2-5min demo w/ fresh-session recall beat, README, 2 public posts (tag @sibylcap + partners)
- Docs: https://sibyllabs.org/get-started
- Discord: https://discord.gg/csya975jMa

## How to register again (if needed) — Playwright Python
The register form is a Next.js server action. Key pitfall: MUST wait for React hydration
(wait_until="load" + ~2.5s) before filling+clicking, else server returns "session expired."
Use chromium executable /opt/data/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome
via /opt/data/.venv-pw/bin/python + playwright.sync_api. Fields: team, email, size,
partnerStacks (Base / "Virtuals Protocol"), idea. Submit button = form button[type=submit].
