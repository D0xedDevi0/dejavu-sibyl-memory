"""THE FLEET deletion test — the multi-agent load-bearing proof.

Same frame, one shared store. With the board intact the allocator coordinates
a de-risk; delete the store and the SAME allocator regresses to naive. This is
the executable gate a judge runs to confirm the fleet's shared memory is
load-bearing (not decorative).

Run:  pytest tests/test_fleet.py -v
"""

import os
import tempfile

from dejavu.fleet import (
    FLEET_TENANT,
    agent_news,
    agent_risk,
    board_stress,
    decay_weight,
    fleet_alloc_decide,
    open_memory,
    read_board,
    run_fleet,
    sleep_consolidate,
    write_view,
)
from dejavu.memory import Memory


def _fresh_db():
    return os.path.join(tempfile.mkdtemp(), "fleet.db")


def _crisis_frame():
    return {"vix": 52.0, "credit_stress": 2.2}


def _calm_frame():
    return {"vix": 18.0, "credit_stress": 0.3}


def _populate(db, crisis=True):
    """Write the news + risk views exactly as a live fleet would."""
    frame = _crisis_frame() if crisis else _calm_frame()
    if crisis:
        n = open_memory(db, "news")
        agent_news(n, headline="credit spreads blowing out, fed on hold",
                   sentiment="risk-off", flags=["spread_widening"])
        n.close()
    else:
        n = open_memory(db, "news")
        agent_news(n, headline="markets calm, spreads contained",
                   sentiment="risk-on", flags=["trend_up"])
        n.close()

    r = open_memory(db, "risk")
    agent_risk(r, credit_stress=frame["credit_stress"], vix=frame["vix"],
               level="high" if crisis else "low")
    r.close()


def test_fleet_board_populates_two_views():
    db = _fresh_db()
    _populate(db)
    a = open_memory(db, "alloc")
    board = read_board(a)
    a.close()
    assert len(board) == 2, f"expected 2 specialist views, got {len(board)}"


def test_allocator_de_risks_when_board_signals_stress():
    db = _fresh_db()
    _populate(db)  # stress views on the board

    a = open_memory(db, "alloc")
    book = fleet_alloc_decide(a, _crisis_frame())
    a.close()

    assert book.equity <= 0.05, f"fleet should de-risk, got equity={book.equity}"
    assert "fleet board" in book.rationale


def test_allocator_stays_invested_on_calm_board():
    db = _fresh_db()
    _populate(db, crisis=False)  # calm views on the board

    a = open_memory(db, "alloc")
    book = fleet_alloc_decide(a, _calm_frame())
    a.close()

    assert book.equity > 0.5, f"calm fleet should stay invested, got equity={book.equity}"


def test_delete_store_fleet_regresses_to_naive():
    """The judge's check: delete the shared store -> empty board -> naive."""
    db = _fresh_db()
    _populate(db)

    # Wipe the shared store before the allocator cold-starts.
    Memory(db, tenant_id=FLEET_TENANT).delete_store()

    a = open_memory(db, "alloc")  # fresh handle on the now-empty store
    board = read_board(a)
    book = fleet_alloc_decide(a, _crisis_frame())
    a.close()

    assert board == []
    assert book.equity > 0.5, \
        f"after deletion the fleet must regress to naive, got equity={book.equity}"


def test_same_frame_diverges_with_and_without_board():
    """Same stressed frame; board present vs absent -> decisions must diverge."""
    db_with = _fresh_db()
    _populate(db_with)
    a = open_memory(db_with, "alloc")
    with_board = fleet_alloc_decide(a, _crisis_frame())
    a.close()

    db_wo = _fresh_db()  # never populated -> deleted/absent store
    a2 = open_memory(db_wo, "alloc")
    without_board = fleet_alloc_decide(a2, _crisis_frame())
    a2.close()

    assert with_board.equity < without_board.equity, \
        f"board should de-risk ({with_board.equity}) below naive ({without_board.equity})"


def test_run_fleet_full_loop_returns_report():
    report = run_fleet(db_path=_fresh_db(), frame=_crisis_frame())
    assert report.board_size == 2
    assert report.book.equity <= 0.05
    assert report.onchain["action"] == "de_risk"


def test_run_fleet_wipe_breaks_coordination():
    report = run_fleet(db_path=_fresh_db(), frame=_crisis_frame(), wipe=True)
    assert report.board_size == 0
    assert report.book.equity > 0.5, \
        f"wiped fleet should be naive, got equity={report.book.equity}"


def test_board_stress_detection():
    stressed = [{"body": {"role": "risk", "level": "high", "vix": 48.0}}]
    calm = [{"body": {"role": "risk", "level": "low", "credit_stress": 0.3}}]
    assert board_stress(stressed) is True
    assert board_stress(calm) is False
    assert board_stress([]) is False


def test_fleet_learner_accepts_a_skill():
    """Lane 4: repeated cycles let the Learner mine the shared journal, and the
    fleet accepts a self-discovered skill — its coordination knowledge compounds."""
    report = run_fleet(db_path=_fresh_db(), frame=_crisis_frame(),
                       learn=True, learn_episodes=4)
    assert report.learned_skill is not None, \
        "fleet --learn should accept a self-discovered skill"
    assert report.learned_skill.get("doc_key", "").startswith("skill/"), \
        f"accepted skill should be a skill doc, got {report.learned_skill}"


# ---- memory-deepening upgrades (supersession / decay / sleep) -------------

def test_write_view_supersedes_conflicting_update():
    """Mem0 four-op analog: a conflicting rewrite archives the old view."""
    db = _fresh_db()
    m = open_memory(db, "news")
    write_view(m, "view", "news/market", {"role": "news", "sentiment": "risk-off"})
    write_view(m, "view", "news/market", {"role": "news", "sentiment": "risk-on"})
    # The active view is the latest; the old one moved to ARCH.
    active = m.get_entity("view", "news/market")
    assert active["body"]["sentiment"] == "risk-on"
    events = m.read_events()
    supersessions = [e for e in events if (e.get("acted") or {}).get("op") == "SUPERSEDE"]
    assert supersessions, "conflicting rewrite must journal a SUPERSEDE event"
    m.close()


def test_decay_weight_damps_stale_views():
    """Retrieval-strength decay: fresh -> boosted, old -> floored, never zero."""
    import time as _t
    fresh = decay_weight(_t.time())
    stale = decay_weight(_t.time() - 10 * 3600 * 24)  # 10 days old
    assert fresh >= 1.0, f"fresh view should rank >=1.0, got {fresh}"
    assert stale < fresh, f"stale view should rank below fresh, {stale} vs {fresh}"
    assert stale >= 0.3, f"decay must floor at 0.3, got {stale}"


def test_sleep_consolidate_reports_health():
    """'Fleet sleep': consolidation pass returns a health report."""
    db = _fresh_db()
    _populate(db)
    report = sleep_consolidate(db, episodes_note="test sleep")
    assert report["deduped"] >= 0
    assert report["note"] == "test sleep"


def test_synthesis_disabled_by_default():
    """LLM skill synthesis is opt-in (FLEET_SYNTH=1): library stays hermetic."""
    import os
    from dejavu import synthesis
    saved = os.environ.pop("FLEET_SYNTH", None)
    try:
        assert synthesis.build_summarizer() is None
        s = synthesis.build_summarizer(enabled=True)
        # None when no endpoint is up; byok-* when the proxy is live.
        assert s is None or getattr(s, "name", "").startswith("byok")
    finally:
        if saved is not None:
            os.environ["FLEET_SYNTH"] = saved
