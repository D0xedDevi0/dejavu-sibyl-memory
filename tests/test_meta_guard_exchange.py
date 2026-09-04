"""L10 META / L11 GUARD / L12 EXCHANGE tests.

Each layer carries a load-bearing proof mirroring the repo's discipline:
the LAYER'S absence degrades behavior, its presence changes the outcome.

  L10 META   : known_unknowns must answer UNKNOWN, not hallucinate coverage.
  L11 GUARD  : even when recall text-misses, the guard BLOCKS the -18% replay.
  L12 EXCHANGE: a store that never lived the crisis imports the lesson and
               cold-starts into the de-risked book (cross-agent transfer).

Deterministic: no LLM, no RNG, no network. Fresh temp stores per test.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from dejavu import exchange, guard, meta
from dejavu.agent import LESSON_NAME, LESSON_TEXT, session_a, session_b
from dejavu.exchange import import_lesson
from dejavu.memory import Memory
from dejavu.policy import naive_book


def _fresh(name="t.db"):
    d = tempfile.mkdtemp()
    return Memory(os.path.join(d, name))


def _seed_crisis(m, *, hard=False):
    """Session-A a store so it owns a real crisis lesson (+optional provenance)."""
    book = session_a(m, {"vix": 52.0, "credit_stress": 2.2})
    if hard:
        meta.record_provenance(m, "lesson", LESSON_NAME, source="backtest",
                               evidence=3, falsifiable=True, hard=True)
    return book


class MetaTest(unittest.TestCase):
    def test_known_unknowns_covered_vs_unknown(self):
        m = _fresh()
        # Empty store: a real query must say UNKNOWN, not fake coverage.
        u = meta.known_unknowns(m, "how to survive a credit crisis")
        self.assertEqual(u["status"], "UNKNOWN")
        self.assertIn("learn", u["action"].lower())

        # After a crisis lesson is recorded -> COVERED (high-confidence hit).
        _seed_crisis(m)
        c = meta.known_unknowns(m, "credit stress crisis lesson")
        self.assertIn(c["status"], ("COVERED", "THIN"))

    def test_coverage_marks_blind_spots(self):
        m = _fresh()
        m.set_entity("fact", "a", {"note": "just a note, no decision"})
        cov = meta.coverage(m)
        self.assertTrue(cov["fact"]["blind"])  # notes-only category is a blind spot
        _seed_crisis(m)
        cov2 = meta.coverage(m)
        self.assertFalse(cov2["lesson"]["blind"])
        self.assertGreaterEqual(cov2["lesson"]["maturity"], 0.3)

    def test_confidence_reflects_provenance(self):
        m = _fresh()
        _seed_crisis(m, hard=True)
        hi = meta.confidence(m, "lesson", LESSON_NAME)
        self.assertGreaterEqual(hi["confidence"], 0.6)  # provenance-backed
        # A bare note with no provenance is far weaker.
        m.set_entity("fact", "f", {"note": "hmm maybe"})
        lo = meta.confidence(m, "fact", "f")
        self.assertLess(lo["confidence"], hi["confidence"])

    def test_snapshot_never_silent(self):
        m = _fresh()
        s = meta.snapshot(m)
        self.assertEqual(s["live_entities"], 0)
        self.assertIn("journal_events", s)
        _seed_crisis(m)
        s2 = meta.snapshot(m)
        self.assertGreaterEqual(s2["live_entities"], 1)


class GuardTest(unittest.TestCase):
    def test_no_hard_lesson_is_permissive_but_honest(self):
        m = _fresh()
        g = guard.guard_book(m, {"vix": 52.0, "credit_stress": 2.2}, 0.55)
        self.assertEqual(g.verdict, "allow")  # nothing to guard against yet
        self.assertIn("no hard lessons", g.rationale)

    def test_guard_blocks_naive_book_in_crisis(self):
        """The load-bearing GUARD proof: a hard crisis lesson + stressed frame
        + proposed naive 0.55 equity => BLOCK, independent of recall text."""
        m = _fresh()
        _seed_crisis(m, hard=True)
        g = guard.guard_book(m, {"vix": 52.0, "credit_stress": 2.2}, 0.55)
        self.assertEqual(g.verdict, "block")
        self.assertTrue(g.blocked)
        self.assertTrue(g.frame_stressed)
        # A defensive book is allowed.
        g2 = guard.guard_book(m, {"vix": 52.0, "credit_stress": 2.2}, 0.05)
        self.assertEqual(g2.verdict, "allow")

    def test_guard_allows_in_calm(self):
        m = _fresh()
        _seed_crisis(m, hard=True)
        g = guard.guard_book(m, {"vix": 18.0, "credit_stress": 0.3}, 0.55)
        self.assertEqual(g.verdict, "allow")  # calm -> not a repeat of the scar


class ExchangeTest(unittest.TestCase):
    def test_export_verify_roundtrip(self):
        seller = _fresh("sell.db")
        _seed_crisis(seller, hard=True)
        art = exchange.export_lesson(seller, LESSON_NAME)
        self.assertEqual(art["schema"], exchange.ARTIFACT_SCHEMA)
        self.assertTrue(art["content_hash"])
        v = exchange.verify_artifact(art)
        self.assertTrue(v["valid"])

        # Tampering breaks verification.
        tampered = dict(art)
        tampered["body"] = {"lesson": "just a tiny note"}
        v2 = exchange.verify_artifact(tampered)
        self.assertFalse(v2["valid"])

    def test_import_gates_and_records_provenance(self):
        seller = _fresh("sell2.db")
        _seed_crisis(seller, hard=True)
        art = exchange.export_lesson(seller, LESSON_NAME)

        buyer = _fresh("buy2.db")
        res = import_lesson(buyer, art)
        self.assertEqual(res["verdict"], "imported")
        # Buyer now has the lesson + provenance pointing at the origin.
        conf = meta.confidence(buyer, "lesson", LESSON_NAME)
        self.assertGreaterEqual(conf["confidence"], 0.6)
        self.assertEqual(conf["provenance"].get("source"), seller.tenant_id)

    def test_import_rejects_tampered_artifact(self):
        buyer = _fresh("buy3.db")
        seller = _fresh("sell3.db")
        _seed_crisis(seller, hard=True)
        art = exchange.export_lesson(seller, LESSON_NAME)
        art["body"] = {"note": "garbage"}
        res = import_lesson(buyer, art)
        self.assertEqual(res["verdict"], "reject")
        self.assertIn("tampered", res["reason"].lower())

    def test_cross_agent_transfer_changes_decision(self):
        """THE load-bearing EXCHANGE proof: a buyer store that never lived the
        crisis imports the seller's lesson, then a fresh cold-start session
        de-risks instead of going naive. Memory travels and changes behavior."""
        # Seller learns the hard way.
        seller = _fresh("sell4.db")
        _seed_crisis(seller, hard=True)
        art = exchange.export_lesson(seller, LESSON_NAME)

        # Buyer never lived it. Naive before import.
        buyer = _fresh("buy4.db")
        frame = {"vix": 52.0, "credit_stress": 2.2}
        naive = session_b(buyer, frame)
        self.assertAlmostEqual(naive.equity, naive_book().equity, places=2)

        # Import the scar tissue, cold-start again -> de-risks.
        res = import_lesson(buyer, art, credit_seller=seller)
        self.assertEqual(res["verdict"], "imported")
        recalled = session_b(buyer, frame)
        self.assertLess(recalled.equity, 0.10,
                        "imported lesson must flip the buyer into de-risk")
        # And the seller earned on the ledger for the transferred lesson.
        ledger = seller.get_state("sovereign/query-ledger")
        paid = 0
        if ledger and isinstance(ledger, dict):
            paid = (ledger.get("body") or {}).get("paid_queries", 0)
        self.assertGreaterEqual(paid, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)