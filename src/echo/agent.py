"""Orchestration loop: session A learns, session B cold-starts and recalls.

This is the two-act structure that produces the demo's money shot:
    Session A — the agent faces a market frame, makes a (naive) decision,
                 takes a loss, and WRITES the distilled lesson to Sibyl.
    Session B — a fresh process with zero chat history cold-starts, QUERIES
                 Sibyl first, recalls the lesson, and DECIDES DIFFERENTLY.

`run_session` can be invoked in-process (tests) or via the `echo` CLI, which
simulates the cold-start by opening a brand-new Memory handle.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from typing import Any

from .base_action import execute
from .config import DEFAULT_DB, Config
from .memory import Memory
from .policy import Book, decide_differently

log = logging.getLogger(__name__)

LESSON_NAME = "crisis-derisking"
LESSON_TEXT = (
    "When credit_stress > 0.7 or vix > 30, staying overweight equity "
    "produces -18%+ drawdown. De-risk to cash/rates instead."
)


def session_a(memory: Memory, frame: dict, *, outcome: dict | None = None) -> Book:
    """Session A: naive decision, painful outcome, WRITE the lesson back."""
    # First call: no memory yet -> the agent takes the naive (long) position.
    book = decide_differently(frame, memory)

    outcome = outcome or {
        "equity_return": -0.18, "credit_return": -0.22, "max_drawdown": -0.24,
    }

    memory.write_lesson(
        LESSON_NAME, LESSON_TEXT, frame=frame, outcome=outcome, status="active",
    )
    memory.write_event(
        evaluated={"vix": frame.get("vix"), "cs": frame.get("credit_stress")},
        acted=book.to_dict(),
        forward="NA",
        extra={"drawdown": outcome["max_drawdown"], "lesson_id": LESSON_NAME},
    )
    log.info("[SESSION A] wrote lesson '%s' + journal event", LESSON_NAME)
    return book


def session_b(memory: Memory, frame: dict, *, phrases: list[str] | None = None) -> Book:
    """Session B: cold start, no conversation history, recall first, decide."""
    return decide_differently(frame, memory, search_phrases=phrases)


def run_sessions(*, crisis_frame: dict | None = None,
                 base_frame: dict | None = None,
                 db_path: str | None = None) -> dict:
    """Full echo loop across two logical sessions on one store.

    Returns a structured dict the demo/tests can assert on.
    """
    crisis = crisis_frame or {"vix": 52.0, "credit_stress": 2.2}
    base = base_frame or {"vix": 18.0, "credit_stress": 0.3}
    db = db_path or os.path.join(tempfile.mkdtemp(), "memory.db")

    # Session A (fresh store).
    a = Memory(db)
    learned_book = session_a(a, crisis)
    a.close()

    # Cold-start: brand-new handle on the SAME store, zero context.
    b = Memory(db)
    recalled_book = session_b(b, crisis)
    b.close()

    return {
        "db": db,
        "crisis_frame": crisis,
        "base_frame": base,
        "learned_book": learned_book.to_dict(),
        "recalled_book": recalled_book.to_dict(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="echo", description="memory-echo loop")
    ap.add_argument("--db", default=None, help="path to memory.db")
    ap.add_argument("--wipe", action="store_true",
                    help="delete store first (simulate no memory)")
    ap.add_argument("--crisis", action="store_true", help="use a crisis frame")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    args = ap.parse_args(argv)

    cfg = Config()
    db = args.db or str(DEFAULT_DB)
    cfg.ensure_dirs()

    if args.wipe and os.path.exists(db):
        os.remove(db)

    crisis = {"vix": 52.0, "credit_stress": 2.2} if args.crisis else \
             {"vix": 18.0, "credit_stress": 0.3}

    # Session A learns only when not wiped (fresh context).
    mem = Memory(db)
    if not args.wipe:
        session_a(mem, crisis)
    mem.close()

    # Cold-start session B on the SAME store.
    mem2 = Memory(db)
    book = session_b(mem2, crisis)
    mem2.close()

    result = {
        "db": db,
        "frame": crisis,
        "equity_weight": book.equity,
        "rationale": book.rationale,
        "loaded": not args.wipe,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"[SESSION B] frame vix={crisis['vix']} cs={crisis['credit_stress']}")
    print(f"[SESSION B] decision: {json.dumps(book.to_dict(), indent=2)}")
    print(f"[SESSION B] equity weight = {book.equity:.2f}  "
          f"({'memory-loaded' if not args.wipe else 'NAIVE - memory wiped'})")
    print(f"[SESSION B] stored DB: {db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
