"""Orchestration loop: session A learns, session B cold-starts and recalls.

This is the two-act structure that produces the demo's money shot:
    Session A — the agent faces a market frame, makes a (naive) decision,
                 takes a loss, and WRITES the distilled lesson to Sibyl.
    Session B — a fresh process with zero chat history cold-starts, QUERIES
                 Sibyl first, recalls the lesson, and DECIDES DIFFERENTLY.

`run_session` can be invoked in-process (tests) or via the `dejavu` CLI, which
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
from .decision import decide_and_execute
from .memory import LESSON_CATEGORY, Memory
from .policy import Book, decide_differently
from .virtuals import exercise as virtuals_exercise

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
                 db_path: str | None = None,
                 config: Config | None = None,
                 virtuals: bool = False) -> dict:
    """Full dejavu loop across two logical sessions on one store.

    Returns a structured dict the demo/tests can assert on.
    """
    crisis = crisis_frame or {"vix": 52.0, "credit_stress": 2.2}
    base = base_frame or {"vix": 18.0, "credit_stress": 0.3}
    db = db_path or os.path.join(tempfile.mkdtemp(), "memory.db")
    config = config or Config()

    # Session A (fresh store).
    a = Memory(db)
    learned_book = session_a(a, crisis)
    a.close()

    # Cold-start: brand-new handle on the SAME store, zero context.
    b = Memory(db)
    recalled_book = session_b(b, crisis)

    # Collect the entity names the policy's recall step surfaced (distinct
    # from the guard's hard-lesson "matched" list).
    recalled_ids: list[str] = []
    for q in config.search_phrases:
        for hit in b.search(q, limit=20):
            if hit.get("category") == LESSON_CATEGORY:
                key = hit.get("key")
                if key and key not in recalled_ids:
                    recalled_ids.append(key)

    # Action authority: the recalled decision is proposed to L11 GUARD.
    # The guard verdict governs what is actually executed, and everything
    # is recorded in a compact, honest decision receipt.
    receipt = decide_and_execute(b, crisis, recalled_book, config,
                                 recalled_ids=recalled_ids)
    b.close()

    # Virtuals ACP coordination: the dejavu agent identity drives the loop.
    v = virtuals_exercise() if virtuals else None

    return {
        "db": db,
        "crisis_frame": crisis,
        "base_frame": base,
        "learned_book": learned_book.to_dict(),
        "recalled_book": recalled_book.to_dict(),
        "receipt": receipt.as_dict(),
        "onchain": receipt.onchain,
        "virtuals": v.as_dict() if v else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dejavu", description="memory-dejavu loop")
    ap.add_argument("--db", default=None, help="path to memory.db")
    ap.add_argument("--wipe", action="store_true",
                    help="delete store first (simulate no memory)")
    ap.add_argument("--crisis", action="store_true", help="use a crisis frame")
    ap.add_argument("--learn", action="store_true",
                    help="after recall, run the Learner and accept the top skill proposal")
    ap.add_argument("--virtuals", action="store_true",
                    help="coordinate the loop through the registered Virtuals dejavu agent")
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

    # Collect the entity names the policy's recall step surfaced.
    recalled_ids: list[str] = []
    for q in cfg.search_phrases:
        for hit in mem2.search(q, limit=20):
            if hit.get("category") == LESSON_CATEGORY:
                key = hit.get("key")
                if key and key not in recalled_ids:
                    recalled_ids.append(key)

    # Action authority: guard -> approved -> onchain, with a compact receipt.
    dec_receipt = decide_and_execute(mem2, crisis, book, cfg,
                                     recalled_ids=recalled_ids)
    mem2.close()

    onchain = dec_receipt.onchain  # backward-compatible onchain dict

    # Optional self-learning beat: scan the journal, propose skills, accept the
    # top one. This is the "dejavu/compounding" moment of the demo.
    accepted = None
    if args.learn:
        m3 = Memory(db)
        report = m3.learn()
        proposals = m3.list_proposals(status="pending")
        if proposals:
            top = proposals[0]
            accepted = m3.accept_proposal(
                top.id, note="dejavu: accepting top self-discovered skill")
        else:
            report = None
        m3.close()

    # Virtuals ACP coordination layer (registered dejavu agent identity).
    v = virtuals_exercise() if args.virtuals else None

    # approved is the book the guard actually authorized for onchain execution.
    approved_book = dec_receipt.approved

    result = {
        "db": db,
        "frame": crisis,
        "equity_weight": approved_book.get("equity", book.equity),
        "rationale": approved_book.get("rationale", book.rationale),
        "loaded": not args.wipe,
        "onchain": onchain,
        "receipt": dec_receipt.as_dict(),
        "learned_skill": accepted,
        "virtuals": v.as_dict() if v else None,
    }
    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0

    print(f"[SESSION B] frame vix={crisis['vix']} cs={crisis['credit_stress']}")
    print(f"[SESSION B] decision: {json.dumps(approved_book, indent=2)}")
    print(f"[SESSION B] equity weight = {approved_book.get('equity', book.equity):.2f}  "
          f"({'memory-loaded' if not args.wipe else 'NAIVE - memory wiped'})")
    print(f"[SESSION B] stored DB: {db}")
    print(f"[ONCHAIN] action={onchain['action']} dry_run={onchain['dry_run']}")
    if onchain.get("tx_hash"):
        print(f"[ONCHAIN] tx {onchain['tx_hash']}")
        print(f"[ONCHAIN] explorer {onchain['explorer_url']}")
    if args.learn:
        if accepted:
            print(f"[LEARN] accepted skill {accepted.get('doc_key')} "
                  f"(proposal {accepted.get('proposal_id')[:8]}...)")
        else:
            print("[LEARN] no skill proposals generated this run")
    if args.virtuals and v:
        print(f"[VIRTUALS] dejavu agent {v.agent_id[:8]}... wallet {v.wallet[:10]}... "
              f"signer={v.signer_policy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
