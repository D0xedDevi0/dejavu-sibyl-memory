"""LANE 1 — "THE FLEET": multi-agent shared-memory blackboard.

Not one agent that remembers — a TEAM of specialist agents coordinated by ONE
shared Sibyl Memory store. No direct agent-to-agent calls: the shared memory
IS the coordination layer.

    news  -> writes a market read to the board      (view/news/market)
    risk  -> writes a stress assessment             (view/risk/stress)
    alloc -> cold-starts, reads the WHOLE board, and decides the book
    exec  -> turns the fleet decision into a real Base onchain action

LOAD-BEARING (the 40-point proof, upgraded to multi-agent): delete the shared
store -> the allocator reads an EMPTY board -> it fails open to the naive
(overweight-equity) book. The fleet's coordination collapses with the memory.

Every agent runs as a FRESH handle on the same store file — zero conversation
context carried between them. The only thing they share is memory. That is the
entire point.

Cross-tenant reads are NOT exposed by the Sibyl client (search/list are
tenant-scoped), so the fleet deliberately uses ONE shared tenant
(`fleet-brain`) with namespace-by-name entity keys (`view/<role>/<signal>`).
See PITFALLS in LANES.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any

from .base_action import execute
from .config import Config, DEFAULT_DB
from .memory import Memory
from .policy import (Book, de_risk_book, is_stressed, naive_book, risk_score)
from .virtuals import exercise as virtuals_exercise

log = logging.getLogger(__name__)

# ---- shared-board namespace -------------------------------------------------
FLEET_TENANT = "fleet-brain"   # ONE tenant so cross-role reads are possible
VIEW = "view"                  # category for specialist views on the board
DECISION = "decision"          # category for the allocator's published book

ROLES = ("news", "risk", "alloc", "exec")

# Retrieval-strength decay (Mem0 Memory Decay analog, Bjork retrieval vs
# storage strength): fresh views rank up to FRESH_BOOST, untouched views
# dampen toward STALE_FLOOR. Nothing is deleted — accessibility falls.
FRESH_BOOST = 1.5
STALE_FLOOR = 0.3
DECAY_HALFLIFE_S = 6 * 3600  # demo-friendly halflife

# Default specialist reads (overridable per run).
DEFAULT_NEWS = {
    "headline": "credit spreads blowing out, fed on hold",
    "sentiment": "risk-off",
    "flags": ["spread_widening", "liquidity_drain"],
}
DEFAULT_RISK = {"credit_stress": 1.9, "vix": 48.0, "level": "high"}


def open_memory(db_path: str, role: str) -> Memory:
    """A FRESH handle on the shared store for `role`.

    All roles open the SAME tenant (`fleet-brain`) so the allocator can read
    every specialist view. `role` is for the event/forward audit trail only.
    """
    return Memory(db_path, tenant_id=FLEET_TENANT)


# ---------------------------------------------------------------------------
# Specialist agents — each writes its read of the world to the shared board.
# ---------------------------------------------------------------------------

def write_view(memory: Memory, category: str, name: str, body: dict) -> dict:
    """Write a view with SUPERSESSION (Mem0 four-op analog).

    If an active view already exists at this key and contradicts the new one,
    the old view is archived to the ARCH tier with a reason and the journal
    records the supersession — contradictions never silently accumulate.
    """
    old = None
    try:
        old = memory.get_entity(category, name)
    except Exception:
        old = None
    if old is not None and isinstance(old.get("body"), dict):
        if old["body"] != body:
            memory.archive_entity(
                category, name, reason=f"superseded by conflicting update"
            )
            memory.write_event(
                evaluated={"key": f"{category}/{name}", "old": old["body"]},
                acted={"op": "SUPERSEDE", "new": body},
            )
    return memory.set_entity(category, name, body, status="active")


def decay_weight(ts: float | None, now: float | None = None) -> float:
    """Exponential retrieval-strength decay: FRESH_BOOST -> STALE_FLOOR."""
    if ts is None:
        return 1.0
    now = now or time.time()
    age = max(0.0, now - ts)
    w = FRESH_BOOST * (0.5 ** (age / DECAY_HALFLIFE_S))
    return max(STALE_FLOOR, w)


def agent_news(memory: Memory, *, headline: str, sentiment: str,
               flags: list[str]) -> dict:
    body = {"role": "news", "headline": headline,
            "sentiment": sentiment, "flags": flags}
    write_view(memory, VIEW, "news/market", body)
    memory.write_event(
        evaluated={"headline": headline, "sentiment": sentiment},
        acted={"flag": "stress" if sentiment == "risk-off" else "calm"},
        forward="alloc",
        extra={"flags": flags},
    )
    log.info("[news] wrote market view to board: %s", headline)
    return body


def agent_risk(memory: Memory, *, credit_stress: float, vix: float,
               level: str) -> dict:
    body = {"role": "risk", "credit_stress": credit_stress, "vix": vix,
            "level": level}
    write_view(memory, VIEW, "risk/stress", body)
    memory.write_event(
        evaluated={"credit_stress": credit_stress, "vix": vix},
        acted={"level": level},
        forward="alloc",
    )
    log.info("[risk] wrote stress assessment: level=%s cs=%s vix=%s",
             level, credit_stress, vix)
    return body


def read_board(memory: Memory | None, *, ranked: bool = True) -> list[dict]:
    """Read the WHOLE fleet board: every specialist view in the shared store.

    With `ranked=True` (default) views are re-ranked by retrieval strength
    (decay_weight over their last-write timestamp): fresh views surface,
    stale views dampen toward STALE_FLOOR — but nothing is deleted. The
    allocator therefore weighs a just-written risk view above an hour-old one.

    Returns [] when there is no memory (deleted store) or no views yet — which
    is exactly what makes the allocator regress to naive.
    """
    if memory is None:
        return []
    try:
        hits = memory.list_entities(VIEW, status="active")
    except Exception:
        # A broken/locked store must not crash the fleet: fail open to naive.
        return []
    if not ranked:
        return hits
    now = time.time()
    def _rank(hit: dict) -> float:
        body = hit.get("body") or {}
        ts = None
        if isinstance(hit.get("updated_at"), (int, float)):
            ts = float(hit["updated_at"])
        elif isinstance(body.get("_ts"), (int, float)):
            ts = float(body["_ts"])
        return -decay_weight(ts, now)
    return sorted(hits, key=_rank)


def sleep_consolidate(db_path: str, *, episodes_note: str = "") -> dict:
    """'Fleet sleep': offline consolidation between episodes.

    Sleep-time-compute analog (Letta): dedupe identical active views, run the
    SDK Linter for store health, and report ARCH-tier supersession counts.
    Pure maintenance — never touches live decision logic.
    """
    m = open_memory(db_path, "sleep")
    try:
        seen: dict[str, str] = {}
        deduped = 0
        for hit in m.list_entities(status="active", limit=1000):
            cat = str(hit.get("category") or "")
            nm = str(hit.get("name") or "")
            key = f"{cat}/{nm}"
            sig = json.dumps(hit.get("body"), sort_keys=True)
            if sig in seen:
                m.delete_entity(cat, nm)
                deduped += 1
            else:
                seen[sig] = key
        from sibyl_memory_client.lint import lint as sdk_lint
        try:
            report = sdk_lint(m.client.storage, tenant_id=FLEET_TENANT)
            findings = {"critical": len(report.critical),
                        "warning": len(report.warnings),
                        "info": len(report.info)}
        except Exception:
            findings = None
        result = {"deduped": deduped, "lint_findings": findings,
                  "note": episodes_note}
        log.info("[sleep] consolidation: %s", result)
        return result
    finally:
        m.close()



def board_stress(board: list[dict]) -> bool:
    """True if any specialist view signals stress (the de-risk trigger)."""
    for hit in board:
        body = hit.get("body") or {}
        if not isinstance(body, dict):
            continue
        if body.get("level") == "high":
            return True
        cs = body.get("credit_stress")
        vix = body.get("vix")
        if cs is not None and float(cs) > 0.7:
            return True
        if vix is not None and float(vix) > 30.0:
            return True
        if body.get("sentiment") == "risk-off":
            return True
    return False


# ---------------------------------------------------------------------------
# The load-bearing fleet decision function.
# ---------------------------------------------------------------------------

def fleet_alloc_decide(memory: Memory | None, frame: dict) -> Book:
    """THE fleet decision function.

    The allocator cold-starts with zero context and reads the shared board. It
    de-risks ONLY when the board carries a coordination signal (a stress view).
    Delete the store -> empty board -> naive overweight-equity.

    This is `decide_differently` generalized from "recall a past lesson" to
    "aggregate the live state of a whole team through memory."
    """
    board = read_board(memory)
    if not board:
        return Book(
            equity=0.55, credit=0.20, rates=0.10, hedges=0.0, cash=0.15,
            rationale="naive: empty fleet board — no coordination, overweight equity",
        )

    stressed = board_stress(board) or is_stressed(frame)
    if stressed:
        return de_risk_book(
            len(board), risk=risk_score(frame),
            rationale=(f"fleet board: {len(board)} specialist view(s) -> "
                       f"coordinated de-risk into cash/rates/hedges"),
        )

    # Calm board + calm frame: the fleet stays invested (but records it).
    return naive_book()


def publish_decision(memory: Memory, book: Book, frame: dict) -> dict:
    """The allocator writes its decision back to the board, closing the loop."""
    body = {"role": "alloc", "frame": frame, "book": book.to_dict()}
    memory.set_entity(DECISION, "alloc/book", body, status="active")
    memory.write_event(
        evaluated={"frame": frame},
        acted=book.to_dict(),
        forward="exec",
    )
    return body


def _cycle(db: str, frame: dict, news: dict, risk: dict) -> tuple[list[dict], Book]:
    """One fleet cycle: specialists write their views (fresh handles), then the
    allocator cold-starts, reads the whole board, and decides."""
    n = open_memory(db, "news")
    agent_news(n, **news)
    n.close()

    r = open_memory(db, "risk")
    agent_risk(r, **risk)
    r.close()

    a = open_memory(db, "alloc")
    board = read_board(a)
    book = fleet_alloc_decide(a, frame)
    publish_decision(a, book, frame)
    a.close()
    return board, book


# ---------------------------------------------------------------------------
# Fleet orchestration.
# ---------------------------------------------------------------------------

@dataclass
class FleetReport:
    db: str
    frame: dict
    board_size: int
    book: Book
    onchain: dict
    learned_skill: dict | None = None
    virtuals: dict | None = None
    sleep: dict | None = None
    roles: list[str] = field(default_factory=lambda: list(ROLES))

    def as_dict(self) -> dict:
        return {
            "db": self.db,
            "frame": self.frame,
            "board_size": self.board_size,
            "book": self.book.to_dict(),
            "onchain": self.onchain,
            "learned_skill": self.learned_skill,
            "virtuals": self.virtuals,
            "roles": self.roles,
        }


def run_fleet(*, db_path: str | None = None, frame: dict | None = None,
              news: dict | None = None, risk: dict | None = None,
              config: Config | None = None, wipe: bool = False,
              learn: bool = False, learn_episodes: int = 4,
              virtuals: bool = False, sleep: bool = True) -> FleetReport:
    """Run the whole fleet on one shared store.

    news + risk each open a FRESH handle, write their view, and close. The
    allocator then opens a FRESH handle (a genuine cold start) and decides from
    the board alone. `wipe=True` deletes the store after the specialists write
    — the demo's "delete the brain and the team falls apart" beat.

    `learn=True` accumulates `learn_episodes` repeated cycles so the Learner has
    journal patterns to mine, then accepts the top self-discovered skill (Lane 4).

    Returns a FleetReport; `onchain` is always a dry-run unless the caller sets
    `Config(dry_run=False)` / `DEJAVU_DRY_RUN=0`.
    """
    db = db_path or os.path.join(tempfile.mkdtemp(), "fleet.db")
    frame = frame or {"vix": 52.0, "credit_stress": 2.2}
    cfg = config or Config()
    cfg.ensure_dirs()
    news_kw = news or DEFAULT_NEWS
    risk_kw = risk or DEFAULT_RISK

    if wipe:
        # Specialists write, then "delete the brain" before the allocator reads.
        n = open_memory(db, "news")
        agent_news(n, **news_kw)
        n.close()
        r = open_memory(db, "risk")
        agent_risk(r, **risk_kw)
        r.close()
        w = open_memory(db, "alloc")
        w.delete_store()
        w.close()
        a = open_memory(db, "alloc")
        board = read_board(a)
        book = fleet_alloc_decide(a, frame)
        publish_decision(a, book, frame)
        a.close()
    else:
        board, book = _cycle(db, frame, news_kw, risk_kw)

    # The fleet decision becomes a real Base onchain action.
    receipt = execute(book, cfg)

    # Optional self-learning beat (Lane 4): accumulate repeated cycles so the
    # Learner has journal patterns to mine, then accept the top skill proposal.
    accepted = None
    if learn:
        for _ in range(learn_episodes):
            _cycle(db, frame, news_kw, risk_kw)
        m = open_memory(db, "alloc")
        m.learn()
        proposals = m.list_proposals(status="pending")
        if proposals:
            accepted = m.accept_proposal(
                proposals[0].id,
                note="fleet: accepting top self-discovered skill",
            )
        m.close()

    v = virtuals_exercise() if virtuals else None
    slept = sleep_consolidate(db) if sleep else None

    return FleetReport(
        db=db,
        frame=frame,
        board_size=len(board),
        book=book,
        onchain=receipt.as_dict(),
        learned_skill=accepted,
        virtuals=v.as_dict() if v else None,
        sleep=slept,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dejavu-fleet",
                                 description="THE FLEET — multi-agent shared-memory blackboard")
    ap.add_argument("--db", default=None, help="path to shared memory.db")
    ap.add_argument("--wipe", action="store_true",
                    help="delete the store after specialists write (break the fleet)")
    ap.add_argument("--crisis", action="store_true",
                    help="use a stressed market frame")
    ap.add_argument("--learn", action="store_true",
                    help="mine the journal and accept the top skill proposal")
    ap.add_argument("--virtuals", action="store_true",
                    help="coordinate through the Virtuals dejavu agent")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    args = ap.parse_args(argv)

    # Live runs get LLM skill synthesis automatically (library/tests stay
    # deterministic unless FLEET_SYNTH=1).
    os.environ.setdefault("FLEET_SYNTH", "1")
    cfg = Config()
    db = args.db or str(DEFAULT_DB).replace("memory.db", "fleet.db")
    frame = {"vix": 52.0, "credit_stress": 2.2} if args.crisis else \
            {"vix": 18.0, "credit_stress": 0.3}

    report = run_fleet(db_path=db, frame=frame, wipe=args.wipe,
                       learn=args.learn, virtuals=args.virtuals, config=cfg)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, default=str))
        return 0

    print(f"[FLEET] board size = {report.board_size} view(s) "
          f"({'wiped -> naive' if args.wipe else 'memory live -> coordinated'})")
    print(f"[ALLOC] decision: {json.dumps(report.book.to_dict(), indent=2)}")
    print(f"[ALLOC] equity weight = {report.book.equity:.2f}")
    print(f"[ONCHAIN] action={report.onchain['action']} "
          f"dry_run={report.onchain['dry_run']}")
    if report.onchain.get("tx_hash"):
        print(f"[ONCHAIN] tx {report.onchain['tx_hash']}")
        print(f"[ONCHAIN] explorer {report.onchain['explorer_url']}")
    if report.learned_skill:
        print(f"[LEARN] accepted skill {report.learned_skill.get('doc_key')}")
    if report.sleep:
        lf = report.sleep["lint_findings"]
        lf_s = "unavailable" if lf is None else (
            f"critical={lf['critical']} warning={lf['warning']} info={lf['info']}")
        print(f"[SLEEP] consolidation: deduped={report.sleep['deduped']} "
              f"lint: {lf_s}")
    if report.virtuals:
        print(f"[VIRTUALS] dejavu agent {report.virtuals['agent_id'][:8]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
