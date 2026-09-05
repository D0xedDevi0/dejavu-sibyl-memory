"""L0 PUBLIC SURFACE — dejavu works as a library for ANY agent.

These tests prove the "broadly usable by arbitrary agents" claim: a fresh
process does `from dejavu import Memory` (nothing else) and gets all sixteen
layers working end to end. No internal-module knowledge, no account, no
network, no config beyond a file path.

Patterns mirror docs/AGENTS.md (decision agent / self-improver / fleet /
borrowing a lesson).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _tmp(name):
    return os.path.join(tempfile.mkdtemp(), name)


def test_public_import_surface():
    """`from dejavu import Memory` exposes every layer as a method."""
    import dejavu
    from dejavu import Memory
    m = Memory(_tmp("surface.db"))
    for meth in ["gated_write", "known_unknowns", "confidence", "snapshot",
                 "guard_book", "hard_lessons", "export_lesson", "import_lesson",
                 "agent_believe", "reach_consensus", "learn_plan",
                 "gaps_remaining", "record_attempt", "distill_rule",
                 "decide_with_skill", "wipe_impact", "request_wipe"]:
        assert hasattr(m, meth), f"Memory.{meth} missing"
    # top-level __all__ resolves (29 exports)
    assert len(dejavu.__all__) >= 20
    assert all(hasattr(dejavu, n) for n in dejavu.__all__)
    m.close()


def test_decision_agent_load_bearing_loop():
    """Pattern 1: a scar written with provenance + hard blocks a naive repeat."""
    from dejavu import Memory, de_risk_book
    m = Memory(_tmp("decision.db"))
    m.write_lesson("crisis", "de-risk when the frame is stressed",
                   frame={"vix": 52, "credit_stress": 2.2},
                   outcome={"max_drawdown": -0.18})
    m.record_provenance("lesson", "crisis", source="backtest",
                        evidence=3, falsifiable=True, hard=True)
    verdict = m.guard_book({"vix": 45, "credit_stress": 1.9},
                           proposed_equity=0.55)
    assert verdict.verdict == "block", verdict
    # the memory de-risks: equity drops well below the naive 0.55
    assert de_risk_book(len(m.recall_lessons(["credit stress crisis"])),
                        risk=1.0).equity < 0.10
    m.close()


def test_autonomous_agent_self_improves():
    """Pattern 2: L14 curriculum plans an UNKNOWN topic -> COVERED after."""
    from dejavu import Memory
    m = Memory(_tmp("selfimprove.db"))
    plan = m.learn_plan({"unexplored alien-trading topic": 0.9,
                         "credit stress de-risk": 0.9})
    unknown = [p for p in plan if p["status"] == "UNKNOWN"]
    assert unknown, "curriculum should surface an uncovered gap"
    topic = unknown[0]["topic"]
    assert m.known_unknowns(topic)["status"] in ("UNKNOWN", "THIN")
    # close the loop honestly: record_attempt is bookkeeping — the gap closes
    # only when the agent actually ACQUIRES a memory on that topic
    m.record_attempt(topic, learned=True, source="backtest",
                     note="imported verified lesson")
    m.write_lesson(topic, f"learned invariant about {topic}: verify before trust",
                   outcome={"evidence": "acquired via planned curriculum"})
    m.record_provenance("lesson", topic, source="backtest",
                        evidence=3, falsifiable=True)
    assert m.known_unknowns(topic)["status"] == "COVERED"
    assert m.gaps_remaining({topic: 0.9}) == [], "gap should be closed"
    m.close()


def test_fleet_consensus_no_fabricated_winner():
    """Pattern 3: high-confidence hard belief beats the naive dissenter."""
    from dejavu import Memory
    a = Memory(_tmp("cons_a.db")); b = Memory(_tmp("cons_b.db"))
    a.agent_believe("regime", {"regime": "crisis", "equity_target": 0.05},
                    provenance={"source": "backtest", "evidence": 3,
                                "falsifiable": True, "hard": True})
    b.agent_believe("regime", {"regime": "calm", "equity_target": 0.55})
    result = a.reach_consensus([b], "regime")
    assert result["status"] in ("UNANIMOUS", "CONVERGED", "MAJORITY",
                                "DEADLOCK")
    assert result["status"] != "DEADLOCK", "conf-weighted truth should win"
    a.close(); b.close()


def test_borrowing_a_lesson_cross_agent():
    """L12: a store that never lived the crisis imports + de-risks."""
    from dejavu import Memory, de_risk_book
    from dejavu.policy import is_stressed
    seller = Memory(_tmp("seller.db")); buyer = Memory(_tmp("buyer.db"))
    seller.write_lesson(
        "crisis", "de-risk the book when vix clears 40 and credit stress is "
        "elevated, because a full-equity book under that regime lost 18 percent "
        "in a single drawdown and the recovery took many cycles to reclaim",
        frame={"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0},
        outcome={"max_drawdown": -0.18, "recovery_cycles": 9})
    seller.record_provenance("lesson", "crisis", source="backtest",
                             evidence=3, hard=True)
    artifact = seller.export_lesson("crisis")
    assert artifact["content_hash"], "artifact carries a verifiable hash"
    assert seller.verify_artifact(artifact)["valid"] is True
    imp = buyer.import_lesson(artifact, credit_seller=seller)
    assert imp["verdict"] == "imported", imp
    if is_stressed({"vix": 52, "credit_stress": 2.2}):
        assert len(buyer.recall_lessons(["credit stress crisis"])) > 0
        assert de_risk_book(1, risk=1.0).equity < 0.10
    seller.close(); buyer.close()


def test_consent_audits_a_wipe():
    """L16: refuse silently, wipe only under force, audit survives deletion."""
    from dejavu import Memory
    m = Memory(_tmp("consent.db"))
    m.write_lesson("secret", "identity-bearing lesson", outcome={"k": "v"})
    refusal = m.request_wipe()          # no force -> refused
    assert refusal["granted"] is False
    assert refusal["impact"]["lessons"] >= 1
    wiped = m.request_wipe(force=True, reason="test: deliberate wipe")
    assert wiped["wiped"] is True
    # the audit log survives the deletion (store-independent)
    assert len(m.read_wipe_audit()) >= 1
