"""dejavu — memory that has a conscience.

One import, all sixteen layers.

The public surface is the :class:`Memory` facade plus the per-layer entry
functions. Any agent can persist, recall, gate, audit, veto, trade, reconcile,
curate, distill, and defend its own memory without knowing the internal module
layout.

Quickstart
----------
.. code-block:: python

    from dejavu import Memory

    m = Memory("agent.db")                 # a fresh store, no account, no network
    m.write_lesson("crisis", "de-risk when vix clears 40", frame={"vix": 52},
                   outcome={"max_drawdown": -0.18})
    m.record_provenance("lesson", "crisis", source="backtest", evidence=3,
                        hard=True)
    m.known_unknowns("what should I do in a credit freeze?")   # COVERED/THIN/UNKNOWN
    if m.guard_book({"vix": 52, "credit_stress": 2.2}, 0.55).verdict == "block":
        ...  # the memory vetoed a repeat of the -18%

See ``docs/AGENTS.md`` for a full drop-in guide.

The sixteen layers
------------------
Act I (L1-L8) — memory you HAVE, OWN + RECALL:
    L1 Sovereign, L2 Identity, L3 Dream, L4 Commons, L5 Regret, L6 Temporal,
    L7 Sovereign Loop, L8 Conflict.
Act II (L9-L16) — memory's relationship with itself and other agents:
    L9 Discernment, L10 Meta, L11 Guard, L12 Exchange, L13 Consensus,
    L14 Curriculum, L15 Distill, L16 Consent.
"""

from __future__ import annotations

from .config import Config
from .memory import Memory, LESSON_CATEGORY

# ---- L9 Discernment ------------------------------------------------------
from .gates import GateDecision, gate_write

# ---- L10 Meta ------------------------------------------------------------
from .meta import (confidence, content_hash, coverage, known_unknowns,
                   record_provenance, snapshot)

# ---- L11 Guard -----------------------------------------------------------
from .guard import GuardVerdict, guard_book, hard_lessons

# ---- L12 Exchange --------------------------------------------------------
from .exchange import export_lesson, import_lesson, verify_artifact

# ---- L13 Consensus -------------------------------------------------------
from .consensus import agent_believe, reach_consensus

# ---- L14 Curriculum ------------------------------------------------------
from .curriculum import gaps_remaining, learn_plan, record_attempt

# ---- L15 Distill ---------------------------------------------------------
from .distill import decide_with_skill, distill_rule

# ---- L16 Consent ---------------------------------------------------------
from .consent import read_wipe_audit, request_wipe, wipe_impact

# ---- Policy (load-bearing decision fn) -----------------------------------
from .policy import naive_book, de_risk_book

__all__ = [
    # core
    "Memory", "LESSON_CATEGORY", "Config",
    # L9
    "GateDecision", "gate_write",
    # L10
    "confidence", "content_hash", "coverage", "known_unknowns",
    "record_provenance", "snapshot",
    # L11
    "GuardVerdict", "guard_book", "hard_lessons",
    # L12
    "export_lesson", "import_lesson", "verify_artifact",
    # L13
    "agent_believe", "reach_consensus",
    # L14
    "gaps_remaining", "learn_plan", "record_attempt",
    # L15
    "decide_with_skill", "distill_rule",
    # L16
    "read_wipe_audit", "request_wipe", "wipe_impact",
    # policy
    "naive_book", "de_risk_book",
]

__version__ = "0.1.0"
