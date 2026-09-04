"""L15 DISTILL + L16 CONSENT tests.

Load-bearing mirrors:

  L15 DISTILL: five credit-stress crisis scars do NOT de-risk a NOVEL pure-
    volatility frame through raw recall (the words never matched), but the
    distilled rule — which never saw a vol spike either — DOES, because it
    learned the shared risk threshold. Memory as judgment, not tape.
    Under-sampling honesty: one scar -> no rule (a curriculum gap, not a guess).

  L16 CONSENT: a silent wipe erases identity + guard memory with no record; a
    CONSENT-guarded wipe refuses until forced, and an authorized wipe journals
    its own destruction to a store-independent log that survives the deletion.

Deterministic: no LLM/RNG/network. Fresh temp stores.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from dejavu import consent, distill
from dejavu.memory import Memory
from dejavu.policy import naive_book


def _fresh(name="d.db"):
    d = tempfile.mkdtemp()
    return Memory(os.path.join(d, name))


def _write_scar(m, name, frame, drawdown=-0.20):
    """A loss-lesson with a structured frame + painful outcome (a scar)."""
    m.write_lesson(name,
                   f"crisis lesson {name}: de-risk when this frame appears",
                   frame=frame, outcome={"max_drawdown": drawdown,
                                         "equity_return": drawdown})


class DistillTest(unittest.TestCase):
    def test_under_sampling_is_honest(self):
        m = _fresh()
        _write_scar(m, "s1", {"vix": 40.0, "credit_stress": 1.0})
        rule = distill.distill_rule(m)  # default min_samples=2
        self.assertIsNone(rule)  # one scar is not a trustworthy rule

    def test_distill_learns_threshold_from_scars(self):
        m = _fresh()
        # Four credit-stress-driven crisis scars (moderate vix).
        for i, cs in enumerate([0.8, 1.1, 1.5, 2.0]):
            _write_scar(m, f"cs{i}", {"vix": 22.0, "credit_stress": cs})
        rule = distill.distill_rule(m)
        self.assertIsNotNone(rule)
        self.assertGreaterEqual(rule["n_lessons"], 4)
        self.assertGreater(rule["threshold"], 0.0)
        self.assertLess(rule["threshold"], 0.9)

    def test_skill_generalizes_to_novel_vol_spike(self):
        """THE L15 load-bearing mirror: raw recall only de-risks on the
        vix/credit_stress signals it was written for. A scar whose risk lives in
        REALIZED VOLATILITY (which is_stressed ignores but risk_score reads) is
        missed by raw recall but caught by the distilled rule, which learned the
        risk threshold as an invariant."""
        m = _fresh()
        # Scars are real losses driven by realized_vol, NOT vix/cs — so the raw
        # decision path (which keys off vix>30 or cs>0.7) never sees them.
        for i in range(3):
            _write_scar(m, f"vol{i}",
                        {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 40.0})
        # Sanity: none of these would individually trip the raw stressed gate.
        from dejavu.policy import is_stressed
        self.assertFalse(is_stressed({"vix": 20.0, "credit_stress": 0.4}))

        # Raw recall on a NOVEL high-vol frame stays NAIVE (vix/cs both low).
        novel = {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 55.0,
                 "yield_slope": 0.5}
        from dejavu.agent import session_b
        raw = session_b(m, novel)
        self.assertGreater(raw.equity, 0.40, "raw recall misses the vol risk")

        # The distilled rule (which never saw a vol spike in this exact shape
        # either) generalizes via the learned risk threshold and de-risks.
        skilled = distill.decide_with_skill(m, novel)
        self.assertLess(skilled.equity, 0.10,
                        "distilled invariant must generalize to the novel frame")
        # A genuinely calm frame does NOT trigger it.
        calm = distill.decide_with_skill(
            m, {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 6.0,
                "yield_slope": 1.5})
        self.assertGreater(calm.equity, 0.30)


class ConsentTest(unittest.TestCase):
    def test_refuses_silent_wipe(self):
        m = _fresh()
        m.write_lesson("guard", "de-risk under stress", frame={"vix": 50},
                       outcome={"max_drawdown": -0.2})
        r = consent.request_wipe(m)
        self.assertFalse(r["granted"])
        self.assertTrue(r["consent_required"])
        self.assertIn("refuses", r["message"])
        # Store is untouched after the refusal.
        self.assertTrue(m.exists)
        self.assertIsNotNone(m.get_lesson("guard"))

    def test_impact_enumerates_what_dies(self):
        m = _fresh()
        m.write_lesson("guard", "never overlong in crisis", frame={"vix": 55},
                       outcome={"max_drawdown": -0.25})
        from dejavu.meta import record_provenance
        record_provenance(m, "lesson", "guard", source="x", evidence=2,
                          falsifiable=True, hard=True)
        imp = consent.wipe_impact(m)
        self.assertGreaterEqual(imp["live_entities"], 1)
        self.assertGreaterEqual(imp["hard_lessons_guarding_harm"], 1)
        self.assertIsNotNone(imp["pre_wipe_content_hash"])
        self.assertIn("identity_id", imp)

    def test_authorized_wipe_is_audited_and_recoverable_by_record(self):
        m = _fresh()
        m.write_lesson("guard", "de-risk", frame={"vix": 50},
                       outcome={"max_drawdown": -0.2})
        log = os.path.join(os.path.dirname(str(m.db_path)), ".wipe-audit.jsonl")
        self.assertFalse(os.path.exists(log))
        r = consent.request_wipe(m, force=True, reason="test: authorized reset")
        self.assertTrue(r["granted"])
        self.assertTrue(r["wiped"])
        self.assertFalse(m.exists)  # gone
        # The audit log survives the deletion, on the parent dir, not in-store.
        audit = consent.read_wipe_audit(m)
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["event"], "MEMORY_WIPED")
        self.assertEqual(audit[0]["reason"], "test: authorized reset")
        self.assertGreaterEqual(audit[0]["impact"]["live_entities"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)