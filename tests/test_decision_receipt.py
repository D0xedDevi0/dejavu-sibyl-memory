"""Action-authority receipt tests.

The receipt is the honest record of one decide->guard->execute cycle:
proposal vs approved allocation, the actual guard verdict, the store's
identifiers/root, and an explicit absent-live-tx signal (no invented evidence).
"""

import os
import tempfile

from dejavu.agent import session_a
from dejavu.config import Config
from dejavu.memory import Memory
from dejavu.policy import decide_differently, de_risk_book, naive_book


def _fresh(name="r.db"):
    return Memory(os.path.join(tempfile.mkdtemp(), name))


def _crisis():
    return {"vix": 52.0, "credit_stress": 2.2}


def test_apply_guard_blocks_naive_proposal():
    """Block verdict → approved allocation is forced to de-risk."""
    from dejavu.decision import apply_guard
    from dejavu.guard import guard_book

    m = _fresh()
    session_a(m, _crisis())  # writes a hard lesson (drawdown -0.24)
    verdict = guard_book(m, _crisis(), naive_book().equity)
    assert verdict.verdict == "block"

    approved = apply_guard(naive_book(), verdict)
    assert approved.equity <= 0.05
    assert "BLOCK" in approved.rationale
    m.close()


def test_apply_guard_allows_defensive_proposal():
    """Allow verdict → proposal is approved unchanged (identity, not copy)."""
    from dejavu.decision import apply_guard
    from dejavu.guard import guard_book

    m = _fresh()
    session_a(m, _crisis())
    defensive = de_risk_book(1, risk=1.0)
    verdict = guard_book(m, _crisis(), defensive.equity)
    assert verdict.verdict == "allow"
    assert apply_guard(defensive, verdict) is defensive
    m.close()


def test_receipt_has_full_authority_chain():
    """DecisionReceipt records all required fields including decision_id."""
    from dejavu.decision import decide_and_execute

    m = _fresh()
    session_a(m, _crisis())
    proposed = decide_differently(_crisis(), m)  # de-risk (equity <= 0.05)
    receipt = decide_and_execute(m, _crisis(), proposed, Config(dry_run=True))
    d = receipt.as_dict()

    required = {"decision_id", "timestamp_utc", "proposed", "guard",
                "approved", "recalled_ids", "memory", "onchain"}
    assert set(d) == required
    assert len(d["decision_id"]) == 16
    assert "T" in d["timestamp_utc"]     # ISO-8601 UTC
    assert d["proposed"]["equity"] <= 0.05
    assert d["guard"]["verdict"] in ("allow", "warn", "block")
    assert d["approved"]["equity"] <= 0.05
    assert isinstance(d["memory"]["tenant_id"], str)
    assert isinstance(d["memory"]["root"], str)
    assert len(d["memory"]["root"]) == 64
    assert d["onchain"]["dry_run"] is True
    assert d["onchain"]["live_tx"] is False
    assert d["onchain"]["tx_hash"] is None  # absent, not invented
    m.close()


def test_receipt_distinguishes_recalled_from_guard_matched():
    """recalled_ids (policy surface) ≠ guard.matched (hard lessons)."""
    from dejavu.decision import decide_and_execute

    m = _fresh()
    session_a(m, _crisis())  # hard lesson "crisis-derisking"

    # Policy text-miss -> empty recalled_ids, but guard still sees hard lesson.
    proposed = decide_differently(
        _crisis(), m, search_phrases=["completely unrelated query that misses"],
    )
    assert proposed.equity > 0.5

    receipt = decide_and_execute(m, _crisis(), proposed, Config(dry_run=True))
    d = receipt.as_dict()

    # Recalled IDs: empty (policy found nothing via FTS).
    assert d["recalled_ids"] == []
    # Guard matched: the hard lesson name (guard scans entities directly).
    assert len(d["guard"]["matched"]) >= 1
    assert "crisis-derisking" in d["guard"]["matched"]
    m.close()


def test_guard_vetoes_text_miss_policy_before_execution():
    """Action authority: when recall text-misses (policy fails open to naive),
    the guard vetoes the naive book so the EXECUTED action de-risks."""
    from dejavu.decision import decide_and_execute

    m = _fresh()
    session_a(m, _crisis())  # hard lesson exists (drawdown -0.24)

    proposed = decide_differently(
        _crisis(), m, search_phrases=["completely unrelated query that misses"],
    )
    assert proposed.equity > 0.5, "policy must fail open to naive on text-miss"

    receipt = decide_and_execute(m, _crisis(), proposed, Config(dry_run=True))
    d = receipt.as_dict()

    assert d["proposed"]["equity"] > 0.5        # proposal is the naive book
    assert d["guard"]["verdict"] == "block"     # guard vetoes it
    assert d["approved"]["equity"] <= 0.05      # approved allocation is de-risked
    assert d["onchain"]["action"] == "de_risk"  # executed action is the safe one
    m.close()


def test_cli_reports_guarded_memory_loaded_allocation():
    """CLI reports the post-guard allocation for a normal recall hit.
    The separate text-miss test exercises BLOCK; this test does not."""
    import json
    import subprocess
    import sys

    db = os.path.join(tempfile.mkdtemp(), "cli.db")
    # Session A writes a hard lesson.
    a = _fresh("cli_a.db")
    # Re-use the same db path pattern:
    a.close()
    from dejavu.agent import main as cli_main
    from dejavu.memory import Memory
    a = Memory(db)
    session_a(a, _crisis())
    a.close()

    # Run the ordinary memory-loaded CLI path, with broadcast disabled.
    proc = subprocess.run(
        [sys.executable, "-m", "dejavu.agent", "--db", db, "--crisis", "--json"],
        capture_output=True, text=True, timeout=60,
        env=dict(os.environ, DEJAVU_DRY_RUN="1", DEJAVU_VIRTUALS_LIVE="0"),
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    # With memory loaded (not wiped), the guard should have approved
    # a de-risked book -> equity <= 0.05.
    assert result["loaded"] is True
    assert result["equity_weight"] <= 0.05, (
        f"CLI equity should be the approved (post-guard) allocation, "
        f"got {result['equity_weight']}"
    )
    assert result["onchain"]["action"] == "de_risk"
    assert result["onchain"]["live_tx"] is False
    assert "receipt" in result
    assert "guard" in result["receipt"]
    ids = result["receipt"]["recalled_ids"]
    assert ids and all(ids), "receipt must contain real nonempty search identifiers"
    assert len(ids) == len(set(ids)), "repeated searches must not duplicate identifiers"