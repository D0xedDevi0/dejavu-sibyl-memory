"""Memory health gate — roadmap #7 (CI).

Runs the SDK `Linter` over a freshly-built fleet store and FAILS on any
critical finding. Wired into CI after the test suite so a corrupted-store
regression (duplicate keys, orphaned ARCH rows, tier violations) breaks the
build instead of shipping.

Exit codes: 0 = clean (or warnings only), 1 = critical findings, 2 = linter
unavailable (treated as failure — a silent gate is no gate).
"""

from __future__ import annotations

import sys
import tempfile

from sibyl_memory_client.lint import lint as sdk_lint

from dejavu.fleet import FLEET_TENANT, open_memory, run_fleet


def main() -> int:
    db = __import__("os").path.join(tempfile.mkdtemp(), "health-gate.db")
    # Build a realistic store: crisis cycle + a learned skill.
    run_fleet(db_path=db, learn=True, learn_episodes=3)

    m = open_memory(db, "health-gate")
    try:
        try:
            report = sdk_lint(m.client.storage, tenant_id=FLEET_TENANT)
        except Exception as exc:  # noqa: BLE001 — gate must not fail silently
            print(f"MEMORY HEALTH GATE: linter unavailable: {exc}")
            return 2

        critical = list(report.critical)
        warnings = list(report.warnings)
        info = list(report.info)
        print(f"MEMORY HEALTH GATE: critical={len(critical)} "
              f"warning={len(warnings)} info={len(info)}")
        for f in critical:
            print(f"  CRITICAL: {f}")
        for f in warnings:
            print(f"  warning: {f}")
        if critical:
            print("MEMORY HEALTH GATE: FAIL")
            return 1
        print("MEMORY HEALTH GATE: PASS")
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    raise SystemExit(main())
