#!/usr/bin/env python3
"""Real two-process Sibyl cold-start/deletion gate for the judge video.

Each phase is an independent process. The shell wrapper prints UTC time and the
Git commit, then executes write -> fresh recall -> destructive wipe -> fresh
recall. Output is intentionally terminal-friendly for an unedited capture.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from dejavu.memory import Memory
from dejavu.policy import decide_differently

TENANT = "judge-gate"
FRAME = {"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0, "yield_slope": 0.6}


def write_phase(db: Path) -> None:
    mem = Memory(str(db), tenant_id=TENANT)
    mem.delete_store()
    mem = Memory(str(db), tenant_id=TENANT)
    mem.write_lesson(
        "crisis-derisking",
        "de-risk to <=5% equity when credit stress spikes",
        frame=FRAME,
        outcome={"averted_drawdown_pct": 18.0},
    )
    print("SESSION A / WRITE")
    print("sibyl.set_entity: lesson/crisis-derisking")
    print("lesson: de-risk to <=5% equity when credit stress spikes")
    print(f"db: {db}")
    mem.close()


def recall_phase(db: Path, label: str) -> None:
    mem = Memory(str(db), tenant_id=TENANT)
    hits = mem.recall_lessons(["credit stress crisis lesson"])
    book = decide_differently(FRAME, mem)
    print(f"{label} / FRESH PID / ZERO CHAT HISTORY")
    print(f"pid: {__import__('os').getpid()}")
    print("sibyl.search: credit stress crisis lesson")
    print(f"lessons_found: {len(hits)}")
    print(f"decision.equity: {book.equity:.2f}")
    print(f"decision.rationale: {book.rationale}")
    mem.close()


def wipe_phase(db: Path) -> None:
    mem = Memory(str(db), tenant_id=TENANT)
    mem.delete_store()
    print("DESTRUCTIVE CONTROL / DELETE SIBYL STORE")
    print(f"deleted: {db}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["write", "recall", "wipe", "recall-wiped"])
    p.add_argument("--db", type=Path, default=Path("/tmp/sibyl-judge-gate.db"))
    args = p.parse_args()
    if args.phase == "write":
        write_phase(args.db)
    elif args.phase == "recall":
        recall_phase(args.db, "SESSION B")
    elif args.phase == "wipe":
        wipe_phase(args.db)
    else:
        recall_phase(args.db, "SESSION C AFTER WIPE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
