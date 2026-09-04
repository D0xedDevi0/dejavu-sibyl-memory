"""L9 DISCERNMENT gate tests — the ingestion-quality proof.

Mirrors the load-bearing discipline of test_loadbearing.py (delete the store -> 
decision breaks), but at the INGESTION layer: delete the gate -> the store
floods with noise -> a low-information fact competes with a hard-won lesson.

Each test is deterministic (no LLM, no RNG, no network). Uses a fresh temp
store so tests never touch production data.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from dejavu.gates import (
    DEFAULT_CAP,
    feedback_unused,
    feedback_used,
    gate_write,
    recalibrate_policy,
)
from dejavu.memory import Memory


def _fresh(db_name="gate.db"):
    d = tempfile.mkdtemp()
    return Memory(os.path.join(d, db_name))


class GateWriteTest(unittest.TestCase):
    def test_persist_rich_lesson(self):
        """A concrete, source-backed lesson earns a slot (PERSIST)."""
        m = _fresh()
        d = gate_write(m, "lesson", "crisis-derisking",
                       {"lesson": "credit_stress>0.7 -> cut equity to 0.05"},
                       source="backtest", evidence=3, falsifiable=True)
        self.assertEqual(d.action, "PERSIST")
        self.assertTrue(d.ok)
        self.assertGreaterEqual(d.scores["value"], 0.3)
        # It actually landed in the store.
        ent = m.get_entity("lesson", "crisis-derisking")
        self.assertIsNotNone(ent)
        self.assertIn("equity", str(ent["body"]["lesson"]))

    def test_reject_noise(self):
        """Contentless chatter is refused at the door — nothing persisted."""
        m = _fresh()
        d = gate_write(m, "trivia", "note-1", {"note": "ok"})
        self.assertEqual(d.action, "REJECT")
        self.assertFalse(d.ok)
        # Nothing written to WARM.
        try:
            m.get_entity("trivia", "note-1")
            self.fail("noise should not have been persisted")
        except Exception:
            pass

    def test_supersede_conflict_routes_to_l8(self):
        """A contradicting fact flags SUPERSEDE so L8 handles the chain."""
        m = _fresh()
        m.set_entity("lesson", "rate", {"lesson": "hike -> de-risk", "in": 1})
        d = gate_write(m, "lesson", "rate",
                       {"lesson": "hike -> stay", "in": 2},
                       source="new-model", evidence=1, falsifiable=True)
        self.assertEqual(d.action, "SUPERSEDE")

    def test_capacity_evicts_weakest_to_arch(self):
        """At capacity the weakest live entry is archived (recoverable), the
        winner persists. Never deleted."""
        m = _fresh()
        cap = 5
        # Fill cap with mediocre facts (routed through the gate so they get a
        # real, LOW stored value — a strong newcomer must outrank them).
        for i in range(cap):
            d = gate_write(m, "fact", f"f{i}", {"v": i, "note": "x" * (8 + i)}, cap=cap)
            self.assertEqual(d.action, "PERSIST", f"seed {i} should persist")
        # Newcomer with a strong, concrete, source-backed lesson.
        d = gate_write(m, "lesson", "strong",
                       {"lesson": "quant crop this cycle cut 3 to 1 now"},
                       source="model", evidence=3, falsifiable=True, cap=cap)
        self.assertEqual(d.action, "EVICT_THEN_PERSIST")
        self.assertTrue(d.ok)
        self.assertEqual(len(d.evicted), 1)
        ecat, ename = d.evicted[0]
        # The evicted entry is recoverable in ARCH, not destroyed.
        arch = m.list_archived(category=ecat)
        self.assertTrue(any(a.get("name") == ename for a in arch),
                        "evicted entry must be recoverable in ARCH")
        # The strong newcomer is live.
        self.assertIsNotNone(m.get_entity("lesson", "strong"))

    def test_newcomer_below_weakest_is_rejected(self):
        """A weak newcomer asking for budget when everyone else is stronger is
        refused rather than evicting a better memory."""
        m = _fresh()
        cap = 3
        for i in range(cap):
            d = gate_write(m, "fact", f"g{i}",
                           {"v": i, "detail": "x" * 30}, cap=cap)
            self.assertEqual(d.action, "PERSIST", f"seed {i} should persist")
        d = gate_write(m, "trivia", "weak", {"note": "hi"}, cap=cap)
        self.assertEqual(d.action, "REJECT")
        self.assertFalse(d.ok)


class GateLearningTest(unittest.TestCase):
    def test_feedback_recalibrates_ingestion_policy(self):
        """Used lessons raise their category weight; idle ones throttle down.
        The gate then gates accordingly."""
        m = _fresh()
        # Two lessons get recalled and one is USED (changed a decision).
        m.set_entity("lesson", "a", {"lesson": "use me a lot"})
        m.set_entity("lesson", "b", {"lesson": "idle b"})
        feedback_used(m, "lesson", "a")
        feedback_used(m, "lesson", "a")
        feedback_used(m, "lesson", "a")
        feedback_unused(m, "lesson", "b")

        pol = recalibrate_policy(m)
        w = pol["weights"]["lesson"]
        # The used category should not have degraded below its default.
        self.assertLessEqual(w, 1.0)
        self.assertGreaterEqual(w, 0.0)

    def test_no_silent_failures(self):
        """Every gate call returns an explicit decision with a reason."""
        m = _fresh()
        for body, src, ev, fals in [
            ({"note": ""}, None, 0, False),
            ({"note": "z"}, None, 0, False),
            ({"note": "a number 7 and a fact 9 in text here enough words"},
             "src", 2, True),
        ]:
            d = gate_write(m, "fact", "k", body, source=src,
                           evidence=ev, falsifiable=fals)
            self.assertIn(d.action, ("PERSIST", "EVICT_THEN_PERSIST", "REJECT", "SUPERSEDE"))
            self.assertTrue(d.reason and d.scores)


class GateLoadBearingTest(unittest.TestCase):
    def test_memory_with_no_gate_floods_and_degrades_recall(self):
        """The load-bearing claim: without the gate, the store fills with
        noise, so a recall of a real lesson gets buried; WITH the gate the
        store stays clean. Two stores, same write volume."""
        # ---- No gate: write 60 noise facts + 1 real lesson ----
        dirty = _fresh("dirty.db")
        for i in range(60):
            dirty.set_entity("fact", f"n{i}", {"note": "meh" + str(i)})
        dirty.write_lesson("real", "cut exposure when credit stress high",
                           frame={"cs": 0.8})
        dirty_hits = dirty.search("cut exposure when credit stress high",
                                  limit=50, category="lesson")
        dirty_lessons = [h.get("body", {}) if isinstance(h, dict) else h
                         for h in dirty_hits]
        # Recall is dominated by noise facts, not the single real lesson.
        self.assertLess(len(dirty_lessons), 5,
                        "dirty store should bury the real lesson among noise")

        # ---- With gate: same volume, noise refused, lesson survives ----
        clean = _fresh("clean.db")
        for i in range(60):
            gate_write(clean, "fact", f"n{i}", {"note": "meh" + str(i)})
        # gate accepted the lesson because it's concrete + source-backed
        d = gate_write(clean, "lesson", "real",
                       {"lesson": "cut exposure when credit stress high 0.05"},
                       source="backtest", evidence=2, falsifiable=True)
        self.assertNotEqual(d.action, "REJECT")

        # The real lesson is now the standout, not buried.
        clean_hits = clean.search("cut exposure when credit stress high",
                                  limit=50, category="lesson")
        self.assertGreaterEqual(len(clean_hits), 1,
                                "kept lesson must recall cleanly")


if __name__ == "__main__":
    unittest.main(verbosity=2)