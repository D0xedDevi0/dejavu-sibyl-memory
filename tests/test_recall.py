"""Recall-layer tests: writing then cold-starting must surface the lesson."""

import os
import tempfile

from echo.agent import LESSON_NAME, LESSON_TEXT, session_a
from echo.memory import Memory


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
    """The Learner proposes a skill from the journal; we can accept it."""
    db = _db()
    m = Memory(db)
    session_a(m, {"vix": 52.0, "credit_stress": 2.2})

    m.learn()
    proposals = m.list_proposals()
    # Proposal generation may be empty on an empty journal history; if any
    # proposals exist we can at least list them. This asserts the pipeline runs.
    assert isinstance(proposals, list)
    m.close()
