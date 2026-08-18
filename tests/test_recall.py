"""Recall-layer tests: writing then cold-starting must surface the lesson."""

import os
import tempfile

from dejavu.agent import LESSON_NAME, LESSON_TEXT, session_a
from dejavu.memory import Memory


def _db():
    return os.path.join(tempfile.mkdtemp(), "memory.db")


def test_write_then_get_roundtrip():
    db = _db()
    m = Memory(db)
    frame = {"vix": 52.0, "credit_stress": 2.2}
    session_a(m, frame)
    got = m.get_lesson(LESSON_NAME)
    assert got["body"]["lesson"] == LESSON_TEXT
    m.close()


def test_search_finds_lesson_across_fresh_handle():
    """A brand-new Memory handle on the same store must find the lesson."""
    db = _db()
    m = Memory(db)
    session_a(m, {"vix": 52.0, "credit_stress": 2.2})
    m.close()

    # Cold start: new handle, same file, zero context.
    m2 = Memory(db)
    hits = m2.search("credit stress crisis")
    assert hits, "search should return the crisis lesson"
    lessons = m2.recall_lessons(["credit stress crisis lesson"])
    assert lessons, "recall_lessons should return the distilled lesson"
    m2.close()


def test_learn_and_accept_proposal():
    """The Learner proposes skills from the journal; we can accept one.

    This is the self-learning / compounding proof: the agent scans its own
    journal and accepts a skill (doc_key `skill/<slug>`) it generated.
    """
    db = _db()
    m = Memory(db)
    # Seed several sessions so the Learner has patterns to detect.
    for _ in range(4):
        session_a(m, {"vix": 52.0, "credit_stress": 2.2})

    report = m.learn()
    proposals = m.list_proposals(status="pending")
    assert report["report"].proposals_made > 0, "Learner must make proposals"
    assert len(proposals) > 0, "pending proposals must exist"

    p = proposals[0]
    # Proposals carry structured fields a real skill can be built from.
    assert getattr(p, "proposed_slug", None)
    assert getattr(p, "proposed_body", None)
    assert getattr(p, "pattern_kind", None)

    res = m.accept_proposal(p.id, note="dejavu test: accept discovered skill")
    assert res["accepted"] is True
    assert res["doc_key"].startswith("skill/"), \
        f"accepted skill should be a skill doc, got {res['doc_key']}"
    m.close()
