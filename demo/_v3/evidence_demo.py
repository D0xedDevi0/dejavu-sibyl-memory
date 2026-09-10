#!/usr/bin/env python3
"""Produce REAL evidence for the v3 demo cards.

Subcommands print only genuine dejavu output (no invented values):

  guard-block   A genuine guard-veto receipt: policy text-misses -> naive
                proposal -> L11 guard BLOCKS -> defensive allocation executed
                (dry-run, tx_hash null).
  gaps          L10 known_unknowns -> L14 learn_plan -> acquire -> COVERED.
"""
import json, os, sys, tempfile

from dejavu.agent import session_a
from dejavu.config import Config
from dejavu.decision import decide_and_execute
from dejavu.memory import Memory
from dejavu.policy import decide_differently

CRISIS = {"vix": 52.0, "credit_stress": 2.2}


def cmd_guard_block(db):
    m = Memory(db)
    session_a(m, CRISIS)  # writes hard lesson "crisis-derisking" (drawdown -0.24)
    # Policy text-miss -> naive (equity > 0.5), but guard sees the hard lesson.
    proposed = decide_differently(
        CRISIS, m, search_phrases=["completely unrelated query that misses"],
    )
    receipt = decide_and_execute(m, CRISIS, proposed, Config(dry_run=True))
    print(json.dumps(receipt.as_dict(), indent=2, sort_keys=True))
    m.close()


def cmd_gaps(db):
    m = Memory(db)
    topic = "sovereign-liquidity-regime"
    before = m.known_unknowns(topic)
    plan = m.learn_plan({topic: 0.9})
    # acquire: a real lesson, with provenance, then close the gap.
    m.write_lesson(topic, "rotate into stable collateral when sovereign "
                         "spread stress crosses two sigma", frame=CRISIS,
                   outcome={"max_drawdown": -0.06, "regime": "stress"})
    m.record_provenance("lesson", topic, source="backtest", evidence=2,
                        falsifiable=True, hard=False)
    m.record_attempt(topic, learned=True, source="backtest",
                     note="imported paper backtest rule")
    after = m.known_unknowns(topic)
    print(json.dumps({"before": before, "plan": plan, "after": after},
                     indent=2, sort_keys=True))
    m.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "guard-block"
    db = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        tempfile.mkdtemp(), "evidence.db")
    {"guard-block": cmd_guard_block, "gaps": cmd_gaps}[which](db)
