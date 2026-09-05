"""L13 CONSENSUS + L14 CURRICULUM tests.

Load-bearing mirrors (each the LAYER's absence-vs-presence proof):

  L13 CONSENSUS:
    - A lone low-confidence dissenting view must NOT overturn a provenance-
      backed hard lesson (CONVERGED on the credible value). Without confidence
      weighting, last-writer-wins or a naive tie would let noise move truth.
    - A genuine unknown split (two ~0.3 claims) returns DEADLOCK — the fleet
      REFUSES a fabricated winner (like L8 refuses silent overwrite).
    - A majority without quorum is honestly labelled MAJORITY, not CONVERGED.

  L14 CURRICULUM:
    - A covered topic has priority 0 and is not in the remaining gaps.
    - An unknown-but-important topic is scheduled above a trivial unknown.
    - The self-improving LOOP: L10 sees UNKNOWN -> L14 plans it -> L12 imports
      the seller's lesson (through the gate) -> L10 now reports COVERED and the
      gap drops out of gaps_remaining. Ignorance -> coverage across one cycle.

Deterministic: no LLM/RNG/network. Fresh temp stores.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from dejavu import consensus, curriculum
from dejavu.agent import LESSON_NAME, session_a
from dejavu.exchange import export_lesson, import_lesson
from dejavu.memory import Memory
from dejavu.meta import known_unknowns, record_provenance


def _fresh(name="c.db"):
    d = tempfile.mkdtemp()
    return Memory(os.path.join(d, name))


def _believer(db, owner_suffix, claim, *, topic="regime", source=None,
              evidence=0, falsifiable=False, hard=False):
    # Each believer is an INDEPENDENT agent -> a distinct tenant identity.
    m = Memory(os.path.join(tempfile.mkdtemp(), f"b{owner_suffix}.db"),
               tenant_id=f"agent-{owner_suffix}")
    consensus.agent_believe(m, topic, claim,
                            provenance={"source": source, "evidence": evidence,
                                        "falsifiable": falsifiable, "hard": hard})
    return m


class ConsensusTest(unittest.TestCase):
    def test_unanimous(self):
        a = _believer("a", "a", {"regime": "calm"})
        b = _believer("b", "b", {"regime": "calm"})
        r = consensus.reach_consensus([a, b], "regime")
        self.assertEqual(r["status"], "UNANIMOUS")
        self.assertEqual(r["converged"], {"regime": "calm"})
        self.assertEqual(r["dissent"], [])

    def test_low_confidence_dissent_does_not_move_truth(self):
        """THE L13 load-bearing mirror: a hard, provenance-backed belief beats a
        lone low-confidence dissenter."""
        hard = _believer("hard", "h", {"regime": "crisis", "equity_target": 0.05},
                         source="backtest", evidence=3, falsifiable=True, hard=True)
        weak = _believer("weak", "w", {"regime": "calm", "equity_target": 0.55})
        r = consensus.reach_consensus([hard, weak], "regime")
        self.assertEqual(r["status"], "CONVERGED")
        self.assertEqual(r["converged"]["equity_target"], 0.05)
        self.assertEqual(len(r["dissent"]), 1)  # dissent preserved, not dropped

    def test_genuine_split_returns_deadlock(self):
        """No quorum + no majority -> DEADLOCK, never a fabricated winner."""
        a = _believer("a", "a", {"side": "left"}, topic="side")
        b = _believer("b", "b", {"side": "right"}, topic="side")
        c = _believer("c", "c", {"side": "center"}, topic="side")  # 3-way split
        r = consensus.reach_consensus([a, b, c], "side")
        self.assertEqual(r["status"], "DEADLOCK")
        self.assertIsNone(r["converged"])

    def test_majority_without_quorum_is_honest(self):
        """3-of-4 agree but no claim hits quorum -> MAJORITY, honestly labelled."""
        a = _believer("a", "a", {"side": "x"}, topic="side")
        b = _believer("b", "b", {"side": "x"}, topic="side")
        c = _believer("c", "c", {"side": "x"}, topic="side")
        d = _believer("d", "d", {"side": "y"}, topic="side")
        r = consensus.reach_consensus([a, b, c, d], "side")
        self.assertEqual(r["status"], "MAJORITY")
        self.assertEqual(r["converged"], {"side": "x"})

    def test_deadlock_not_written_to_consensus_store(self):
        a = _believer("a", "a", {"side": "l"}, topic="side")
        b = _believer("b", "b", {"side": "r"}, topic="side")
        coord = _fresh("coord.db")
        r = consensus.reach_consensus([a, b], "side", consensus_memory=coord)
        self.assertEqual(r["status"], "DEADLOCK")
        # Coordinator records CONTESTED, not a fabricated consensus entity.
        ent = coord.get_entity(consensus.CONSENSUS_CATEGORY, "side")
        self.assertEqual(ent["body"]["status"], "CONTESTED")


class CurriculumTest(unittest.TestCase):
    def test_covered_topic_has_zero_priority(self):
        m = _fresh()
        session_a(m, {"vix": 52.0, "credit_stress": 2.2})  # learn the crisis lesson
        plan = curriculum.learn_plan(m, {"crisis-de-risk": 0.9})
        covered = [g for g in plan if g["topic"] == "crisis-de-risk"][0]
        self.assertEqual(covered["status"], "COVERED")
        self.assertEqual(covered["priority"], 0.0)

    def test_unknown_important_outranks_unknown_trivial(self):
        m = _fresh()  # empty -> everything UNKNOWN
        plan = curriculum.learn_plan(m, {"alpha-lane-A": 0.9, "alpha-lane-B": 0.1})
        self.assertEqual(plan[0]["topic"], "alpha-lane-A")
        self.assertGreater(plan[0]["priority"], plan[1]["priority"])

    def test_gaps_remaining_excludes_covered(self):
        m = _fresh()
        session_a(m, {"vix": 52.0, "credit_stress": 2.2})
        m.set_reference("curriculum/gap/other", {"topic": "other", "learned": True})
        rem = curriculum.gaps_remaining(m, {"crisis-de-risk": 0.9, "other": 0.5})
        topics = [g["topic"] for g in rem]
        self.assertNotIn("crisis-de-risk", topics)  # covered -> no gap
        self.assertIn("other", topics)

    def test_self_improving_loop_ignorance_to_coverage(self):
        """THE L14 load-bearing capstone: L10 sees UNKNOWN -> L14 plans ->
        L12 imports the seller's verified lesson through the L9 gate -> L10
        now reports COVERED and the gap is gone from the curriculum."""
        # Seller learned the crisis lesson the hard way.
        seller = _fresh("sell_loop.db")
        session_a(seller, {"vix": 52.0, "credit_stress": 2.2})
        record_provenance(seller, "lesson", LESSON_NAME, source="backtest",
                          evidence=3, falsifiable=True, hard=True)
        art = export_lesson(seller, LESSON_NAME)

        # Buyer starts ignorant.
        buyer = _fresh("buy_loop.db")
        ku_before = known_unknowns(buyer, "how to survive a credit crisis")
        self.assertEqual(ku_before["status"], "UNKNOWN")

        # Curriculum plans to learn it (important).
        plan = curriculum.learn_plan(buyer, {"crisis-derisking": 0.9})
        gap_topic = plan[0]["topic"]
        self.assertEqual(gap_topic, "crisis-derisking")
        self.assertEqual(plan[0]["status"], "UNKNOWN")

        # Acquire via L12 (verify + gate + provenance).
        res = import_lesson(buyer, art)
        self.assertEqual(res["verdict"], "imported")

        # Now COVERED: the loop closed.
        ku_after = known_unknowns(buyer, "how to survive a credit crisis")
        self.assertEqual(ku_after["status"], "COVERED")
        rem = curriculum.gaps_remaining(buyer, {"crisis-derisking": 0.9})
        self.assertNotIn("crisis-derisking", [g["topic"] for g in rem])


if __name__ == "__main__":
    unittest.main(verbosity=2)