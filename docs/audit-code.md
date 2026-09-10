# THE SPINE — bounded code audit

Status: local, uncommitted, unpublished. Starting HEAD `97402cbc1e68a046a8de36fcbe0a49e9912e9534`. Raw final outputs: [final-verification.json](evidence/final/final-verification.json). Independent review returned FAIL against an earlier worktree snapshot. Its blocking findings have been corrected and verified by the parent, as recorded below; no subsequent independent PASS is claimed.

## Changes inspected and exercised by parent

- `src/dejavu/decision.py::decide_and_execute`: policy proposal → `guard_book` → `apply_guard` → Base adapter. Captures memory root before adapter execution. Receipt separates proposed/approved books, guard verdict/matches, supplied recall identifiers, root/tenant/path, timestamp and transaction fields.
- `src/dejavu/agent.py::main`, `run_sessions`: route the action through the wrapper instead of calling the Base adapter directly. CLI displays approved equity. The logical two-handle helper is not itself fresh-process proof.
- `src/dejavu/base_action.py::OnchainReceipt.as_dict`: adds `live_tx`; this denotes a returned broadcast hash, NOT mined confirmation. Dry run preserves null transaction hash. Adapter performs symbolic dust transfers, not portfolio trading.
- `src/dejavu/virtuals.py::acp_available`, `exercise`: live ACP requires explicit opt-in; unavailable signer no longer reports available=true. Unit tests explicitly unset live mode.
- `tests/test_onchain.py`: signing uses an ephemeral test account rather than a production key path.
- `tests/test_decision_receipt.py`: tests guard BLOCK/ALLOW, receipt fields, recall-miss veto and ordinary CLI reporting. The CLI test does NOT itself force a guard BLOCK; its name/comments were corrected.
- `tests/test_subprocess_gate.py`: genuine write/recall/wipe/recall subprocesses, separate recall PIDs, default-wrapper execution/cleanup, refusal to overwrite an existing file.
- `demo/run_continuous_gate.sh`: UTC/revision/worktree label, assertions before success, configurable interpreter, isolated default temporary directory and refusal to overwrite an existing path. Cleanup removes only its own temporary directory, not an explicit user path.

## Parent-found wrapper defect, RED → GREEN

The worker's first implementation used `mktemp` to create a file, then rejected every default run because that file already existed. Parent added `test_wrapper_default_runs_and_cleans_owned_directory`, observed `1 failed, 2 passed` with the exact existing-file refusal, then used `mktemp -d` plus a not-yet-created child database. Targeted rerun: `3 passed in 1.03s`.

## Final actual execution

```text
Local full suite: 150 passed, 3 skipped in 37.45s
Sanitized environment: 144 passed, 9 skipped in 40.03s
Git diff --check: exit 0
```

Local skips are three opt-in live ACP checks. Sanitized run additionally skips six tests for the undeclared optional sibling NEURAL_MESH installation. Sanitized HOME, nonexistent wallet-key path and sibling root, dry-run mode, explicit source PYTHONPATH, and fresh declared-dependency venv were used. Do not advertise 153 passes or claim skipped partner checks passed.

Default wrapper, UTC `2026-09-10T04:24:53Z`:

```text
WORKTREE: dirty — uncommitted changes present
SESSION B pid: 1454
lessons_found: 1
decision.equity: 0.02
SESSION C AFTER WIPE pid: 1461
lessons_found: 0
decision.equity: 0.55
GATE RESULT: Sibyl present => equity <=0.05; Sibyl deleted => equity 0.55
exit 0
```

Values printed by the terminal are rounded. Full-frame allocation is approximately 0.0241542; simplified CLI frame gives 0.05. The same fixed full frame is used on both sides of the deletion experiment.

## Additional receipt defect caught by wheel smoke

The first installed-wheel smoke emitted `recalled_ids: ["", ""]`: Sibyl search hits use `key`, not `name`. Parent added nonempty/deduplicated ID assertions, observed the expected test failure, then corrected both orchestration paths to collect real search keys. Final rebuilt wheel reports `["crisis-derisking"]`, dry-run true and null transaction hash. Final full suites were rerun after this correction.

## Independent review disposition

The independent reviewer correctly rejected its earlier snapshot for empty/duplicate recall identifiers and an unpinned CLI subprocess that could inherit live mode. Both fixes were already present when its delayed report arrived; parent read back the exact current files and reran the relevant tests.

- Recall identifiers: both `agent.py` paths now use `key` and deduplicate. CLI regression asserts nonempty unique IDs; installed-wheel output proves `crisis-derisking`.
- Subprocess safety: CLI test explicitly pins `DEJAVU_DRY_RUN=1` and `DEJAVU_VIRTUALS_LIVE=0`.
- Misnamed coverage: renamed to normal memory-loaded CLI behavior; no claim that this CLI test exercises BLOCK. Direct guard-veto test covers BLOCK.
- Virtuals portability: deterministic tests explicitly unset live opt-in.
- Empty memory remaining fail-open is intentional, documented demo behavior, not production safety.
- Reviewer confirmed guard → approved allocation → executor wiring. Parent follow-up output is `evidence/final/review-followup.json`. The independent verdict itself remains historical FAIL, not retroactively PASS.
- Remaining non-blocking limitation: `timestamp_utc` and `decision_id` are generated after the adapter returns, so timestamp denotes receipt completion, not pre-action authorization time. Root is captured before the adapter. Same-second ID collisions remain possible.
- No additional CLI feature was added merely to force text-miss coverage. Default interpreter requires the documented `.venv` setup or `PYTHON` override.

## Scope and limits

- No real transaction, paid endpoint call, publication or submission was performed.
- The no-memory fallback intentionally stays naive; this is not a production fail-closed risk controller.
- A guard BLOCK replaces the proposed allocation with a defensive allocation; it does not halt all actions.
- Decision root is an unsigned state fingerprint, not proof of truthful memory or atomic transaction authorization. Concurrent mutation is not locked across the whole decision flow.
- Receipt recall identifiers are collected by an additional search, not instrumented directly out of the policy recall. Custom phrase configurations and concurrent writes need stronger provenance before production claims.
- `decision_id` uses second-resolution timestamp/proposal/root and may collide for identical same-second decisions; it is a trace label, not a uniqueness/security guarantee.
- Current code tests do not retroactively validate historical transactions or the old public video.
- Optional ACP checks are skipped, not independently verified live integration.
