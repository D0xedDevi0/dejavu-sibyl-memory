# THE SPINE — final technical and submission audit

Audit date: 2026-09-10 UTC. Starting revision: `97402cbc1e68a046a8de36fcbe0a49e9912e9534`, initially clean `main`. Local changes are **uncommitted and unpublished**. No external state was changed.

## Recommendation

**STOP new feature development. HOLD final submission claims until the release blockers below are cleared.** The core memory mechanism is real and reproducible. Evidence quality and honest packaging—not another subsystem—are the highest-return work.

This audit does not declare the project disqualified, production-safe, or guaranteed to win. Eligibility belongs to the organizers. No private build-page state was verified.

## Acceptance contract

Official sources: [event](https://hack.sibyllabs.org/) and [submission requirements](https://hack.sibyllabs.org/submissions), fetched during this audit; raw submission-page content in `evidence/final/official-submission-rules.json`.

🟦 Deadline: September 10, 2026, 23:59 UTC.
🟦 Mandatory: real Sibyl persistence and use in a genuinely fresh session; deleting memory materially breaks the claimed function.
🟦 Public MIT/Apache repository, README, 2–5 minute demo, public build posts, and private build page marked ready.
🟦 Rubric: 40 memory / 25 innovation / 20 execution / 15 pitch; up to 10 genuine PMF bonus. Partner multiplier requires real work visible to judges, not imports or registration alone.

Continuous terminal proof with UTC and code revision is the evidence standard used here. Do not attribute a stronger literal requirement to the official rules unless the full official wording supports it.

## Findings and disposition

### P0 — release blockers

1. **Eligibility uncertainty.** Of 86 preserved commits, 64 predate September 1; first commit is August 17. Core integration and earlier media already existed. Corrected prior-work declarations; organizer clarification still needed. Never rewrite history.
2. **Historical film contains a false external-customer inference.** At ~02:49 it says “someone outside us paid.” USDC Transfer logs show the team's own wallet paid both times. The canonical local v3 replacement removes that claim; the historical public video remains unchanged until an authorized publication.
3. **Final local revision not published.** Remote CI is green only for the original September 5 revision. No push was authorized. Final local code/tests must be verified, reviewed, then committed/pushed only with authorization; remote CI must match.
4. **Private submission state unverified.** `_scripts/check_ready.py` needs more than Playwright: it contains `PASTE_BUILD_TOKEN` and an obsolete hard-coded browser path. No guessed credentials or ready-state claims. Owner must provide authenticated access or verify the saved form.
5. **Qualifying posts unresolved.** Three historical candidates are listed; two predate the build window and the September one does not establish every Base-only tag requirement. Verify exact content/timing/tags; publish qualifying corrections only with authorization.

### P1 — credibility and technical corrections

🟦 **Symbolic action, not trading:** Base adapter sends 1,000 wei. Both cited old action receipts are self-transfers. They do not prove a portfolio rebalance or the current guard/recipient branch.
🟦 **Static paid snapshot:** endpoint source hardcodes root/layer/benchmark metadata and `asset_resolves`; no live SQLite query or response-wide cryptographic attestation.
🟦 **Benchmark denominator:** legacy “12 crises” sequence actually alternates six crisis and six zero-return calm periods. Return means average twelve periods. Corrected active docs without changing historical results.
🟦 **Frame mismatch:** full continuous-proof frame returns approximately 0.0241542 equity, displayed 0.02; simplified CLI frame returns 0.05. Kept policy intact and distinguished the numbers.
🟦 **Test portability:** baseline clean archive passed 142 tests on this host, but sanitized HOME/key/sibling settings exposed two environment-dependent tests. Raw failure evidence is retained, not hidden. Final code pass addresses private-key and ACP dependencies.
🟦 **Guard wiring:** initial `agent.main` / `run_sessions` executed directly, bypassing L11. A bounded decision-receipt wrapper is the only new feature lane. Final behavior and tests are recorded in `audit-code.md`.
🟦 **Safety boundaries:** owner deduplication is not permissionless identity; hashes are not trusted authorship; pattern scans are not complete poison defenses; consent is not filesystem security; no-memory fallback remains intentionally naive.

## Verified baseline and reproducibility

Baseline source archive + fresh declared-dependency venv:

```text
142 passed in 43.49s
```

Sanitized environment before fixes:

```text
2 failed, 134 passed, 6 skipped in 57.69s
```

Failures: hardcoded wallet-existence test loaded a different configured path; ACP test assumed installed CLI implied authenticated signer. See `evidence/final/baseline-isolated-tests.txt`.

Wheel built and installed into a separate venv; dry-run CLI from `/tmp` returned equity 0.05 with `tx_hash:null`, no wallet key. Build emitted an existing setuptools license-table deprecation warning, not failure. `pip` is absent in these uv venvs; installation used `uv pip`, not a fabricated pip success.

Final post-change verification: **150 passed, 3 skipped** locally; **144 passed, 9 skipped** in the sanitized environment. The additional six skips require the optional sibling NEURAL_MESH checkout; three are opt-in live ACP. The default wrapper passed with separate recall PIDs and 0.02 / 0.55 displayed equity. Raw output is in `evidence/final/final-verification.json` and [code audit](audit-code.md). A final wheel smoke test is saved separately; baseline evidence is not substituted for these results.

## Reproduced metrics

From actual scripts (`evidence/final/ablations.txt`):

🟦 200-frame ablation: 150 stressed, −2.828% with memory / −9.900% without, 7.072 percentage points difference, 75% changed decisions.
🟦 Spine sequence: 0.8176 / 0.4887 capital, 1.67× remaining-capital ratio, six crisis plus six calm periods. Mean over all periods −1.650% / −5.625%.
🟦 Conscience panel: 3/3 selected recall-blind frames caught by the distilled rule; full arm capital 0.8013 / first-act 0.6282 / no-memory 0.4887.

These use constructed fixtures and toy return models. They are not realized trading returns, broad generalization tests, or independent validation of all sixteen layers.

## Public verification

Read-only parent verification saved complete raw responses in `evidence/final/external-verification.json`:

🟦 Repository public, MIT; remote CI run `33981988969` success on initial revision.
🟦 Public video HTTP 200; downloaded bytes exactly match local; checksum in surface audit.
🟦 Five historical Base receipts status 1. Token logs prove self-funded x402 tests.
🟦 Unpaid endpoint HTTP 402, Base, USDC amount 10000.
🟦 Inventory covers all 44 MP4 files: five candidates and 39 intermediate segments.

[Surface audit](audit-surfaces.md) contains exact durations, timestamps, limitations and evidence handles.

## Actual local documentation changes

🟦 Rewrote README with proof first, three reproduced claims, architecture, safety limits, partner scope, market hypothesis, reproducibility and accurate prior work.
🟦 Replaced judge sheet with a code/test/evidence matrix and explicit missing video timestamps.
🟦 Replaced PMF claim with decoded-payment attribution and a measurable pilot proposal.
🟦 Replaced submission copy and unchecked unverified saved/ready claims.
🟦 Marked BUILD_SPEC, CONCEPT, LANES and UPGRADES historical rather than competing sources of truth.
🟦 Corrected showcase/Doctrine boundaries without treating metaphors as capabilities.
🟦 Added surface audit, raw evidence and the [2:30 final script](final-demo-script.md).

## Independent review closure

The reviewer rejected an earlier snapshot for empty/duplicate receipt IDs and an unpinned CLI subprocess. Parent verified both fixes in the current source and reran the focused suite; details and remaining timestamp/provenance limitations are in [code audit](audit-code.md). The test name now accurately describes normal recall coverage. No subsequent independent PASS is claimed, and no public-release blocker was removed by this local closure.

## Ranked remaining work

1. **Obtain organizer eligibility clarification** and authenticated submission read-back. External human/access dependencies; cannot be manufactured locally.
2. **Publish the verified replacement media.** Local v3 is 133.523220 seconds (2:13), includes the captured fresh-process proof, actual guard receipt, historical transaction labels and simulated-metric labels. It still requires authorized publication and a post-push public read-back.
3. **Authorize publication of reviewed local changes.** Commit code first, capture code revision honestly, commit media separately, push, verify exact remote CI and public links.
4. **Verify/post qualifying public artifacts** with accurate partner and PMF language, only after authorization.
5. **Read back the final build page and mark ready before deadline**, only with explicit authorization.

Do not add a new database, contract, LLM provider, Hermes integration or benchmark. A named external operator pilot is the next commercial milestone, not a last-hour pretext for an unearned PMF bonus.

## Risk register

| Risk | Severity | Mitigation / owner |
|---|---|---|
| Pre-window work interpretation | Critical eligibility uncertainty | Organizer clarification, user |
| False external-customer scene remains public | High credibility | Replace film before authorized release |
| Local revision differs from public submission | High | Authorized push + matching remote CI |
| Private ready state unknown | High | Authenticated exact-target read-back |
| Posts do not satisfy timing/tags | High | Verify actual content; authorized corrections |
| Dust transfer mistaken for hedge | High | Narrow wording and visible historical labels |
| Toy returns mistaken for real alpha | High | State fixture/model/denominator on-screen |
| New receipt mistaken for confirmed chain proof | High | Null dry-run tx; separate confirmation state |
| Heuristic defenses overclaimed | Medium | Explicit threat-model limits; no safety guarantee |
| Old plans conflict with active docs | Medium | Historical notices; current README/judge canonical |
| No independent pilot | Medium scoring | Honest market hypothesis; do not claim PMF proven |

## Final submission checklist

See `SUBMISSION.md` for exact form copy and the unchecked release steps. The final report should distinguish **local verified improvement** from **public release ready**. The latter is not established by this audit.
