#!/usr/bin/env python3
"""dejavu ACP PROVIDER fulfillment — turn a hired requirement into a
memory-grounded verdict using the REAL dejavu pipeline.

The dejavu agent (ACP, Base) now lists the offering
"Sibyl Memory De-Risk Verdict" ($0.50, fixed, required funds). When another
agent hires it, this module is the brain behind the deliverable:

    requirement  = { query: str, frame: {vix, credit_stress, realized_vol,
                                          yield_slope?} }
    deliverable  = { recalled_lessons, equity_target, rationale,
                     guard_verdict, distill_generalized }

It runs the actual Sibyl 16-layer memory stack (Memory recall + policy
decision + L11 guard + L15 distill) — the same code the hackathon proof uses —
so a hired verdict is grounded in memory, not a canned reply.

Provider lifecycle (acp-cli): `acp events listen` / job watch sees a hire →
`provider set-budget --job-id <id> --amount <price>` → this `fulfill()` →
`provider submit --job-id <id> ...`. This module is the pure "compute the
deliverable" step; the on-chain submit is a thin shell on top.

Self-test (no network, no spend):
    python virtuals/provider_runtime.py --self-test
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from dejavu.memory import Memory
from dejavu.policy import decide_differently, is_stressed, risk_score
from dejavu.guard import guard_book
from dejavu.distill import decide_with_skill
from dejavu.meta import record_provenance

HERE = Path(__file__).resolve().parent
# seed store (the dejavu memory layer's accumulated scar tissue)
SEED_DB = os.environ.get("DEJAVU_SEED_DB", str(HERE / "dejavu-memory.db"))


def _ensure_seed(mem: Memory) -> None:
    """Ensure the memory layer has its crisis scars + hard lesson (idempotent).
    If a persisted seed exists this is a no-op; fresh stores get the canonical
    scar tissue so recall/guard/distill have something load-bearing to run on."""
    if mem.list_lessons():
        return
    mem.write_lesson("crisis-1",
                     "de-risk to <=5% equity when credit stress spikes or vix>30",
                     frame={"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0,
                            "yield_slope": 0.6},
                     outcome={"max_drawdown": -0.24})
    record_provenance(mem, "lesson", "crisis-1", source="backtest",
                      evidence=3, falsifiable=True, hard=True)
    for i, (vix, cs, vol, slope) in enumerate([
            (20.0, 0.4, 42.0, 1.2), (24.0, 0.5, 38.0, 1.0),
            (18.0, 0.6, 45.0, 0.9),
    ]):
        mem.write_lesson(
            f"vol-scar-{i}",
            f"realized-vol scar {i}: equity bled on the tape gapping",
            frame={"vix": vix, "credit_stress": cs, "realized_vol": vol,
                   "yield_slope": slope},
            outcome={"max_drawdown": -0.18})


@dataclass
class MemoryVerdict:
    recalled_lessons: int
    equity_target: float
    rationale: str
    guard_verdict: str
    distill_generalized: bool
    stressed: bool
    risk: float
    memory_root: str | None = None

    def as_deliverable(self) -> dict:
        return asdict(self)


def fulfill(requirement: dict) -> dict:
    """Compute the memory-grounded verdict for a hired requirement.

    requirement keys: query (str), frame (dict with vix + credit_stress, and
    optional realized_vol / yield_slope). Returns the offering deliverable.
    """
    query = requirement.get("query", "credit stress crisis lesson de-risk")
    frame = requirement.get("frame", {})
    if not isinstance(frame, dict) or "vix" not in frame or \
            "credit_stress" not in frame:
        frame = {"vix": float(frame.get("vix", 52.0)),
                 "credit_stress": float(frame.get("credit_stress", 2.2)),
                 "realized_vol": float(frame.get("realized_vol", 34.0)),
                 "yield_slope": float(frame.get("yield_slope", 0.6))}

    db = os.environ.get("DEJAVU_PROVIDER_DB") or \
        os.path.join(tempfile.mkdtemp(), "provider.db")
    mem = Memory(db, tenant_id="dejavu-provider")
    mem.delete_store()          # clean, self-contained store per call
    mem = Memory(db, tenant_id="dejavu-provider")
    _ensure_seed(mem)
    try:
        # L1-L8 recall drives the headline decision; then the conscience stack.
        recalled = mem.recall_lessons([query, "credit stress crisis lesson"])
        book = decide_differently(frame, mem, search_phrases=[query])
        verdict = guard_book(mem, frame, proposed_equity=book.equity)
        skill = decide_with_skill(mem, frame)
        equity = book.equity
        if verdict.verdict == "block":
            equity = 0.05
        if skill.equity < equity:
            equity = skill.equity

        stressed = is_stressed(frame)
        distilled = skill.equity < 0.10 and not stressed  # generalized to a blind channel
        rationale = book.rationale
        if verdict.verdict == "block":
            rationale += " | L11 GUARD vetoed the overweight book"
        if skill.equity < book.equity:
            rationale += " | L15 DISTILL caught a recall-blind risk channel"
        root = ""
        try:
            from dejavu.sovereign import memory_root
            root = memory_root(mem)["root"]
        except Exception:
            root = ""
        return asdict(MemoryVerdict(
            recalled_lessons=len(recalled),
            equity_target=round(equity, 4),
            rationale=rationale,
            guard_verdict=verdict.verdict,
            distill_generalized=bool(distilled),
            stressed=stressed,
            risk=round(risk_score(frame), 3),
            memory_root=root,
        ))
    finally:
        mem.close()


def _self_test() -> int:
    cases = [
        {"query": "credit stress crisis lesson", "frame": {"vix": 52.0, "credit_stress": 2.2}},
        {"query": "the tape gapped", "frame": {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 55.0, "yield_slope": 0.5}},
        {"query": "calm regime", "frame": {"vix": 14.0, "credit_stress": 0.3}},
    ]
    ok = True
    for c in cases:
        d = fulfill(c)
        print(json.dumps({"req": c, "deliverable": d}, indent=2))
        # schema invariants
        for req in ("equity_target", "rationale", "recalled_lessons",
                    "guard_verdict", "distill_generalized"):
            if req not in d:
                ok = False
                print(f"  !! missing {req}")
        if not (0.0 <= d["equity_target"] <= 1.0):
            ok = False
    print("SELF-TEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    # one-shot from a requirement file (for cron / listener wiring)
    req = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}
    print(json.dumps(fulfill(req), indent=2))
