"""Tests for the fused Sovereign Memory spine (six layers, one arc)."""

from __future__ import annotations

from dejavu.spine import run_arc


def test_spine_arc_full(tmp_path):
    out = run_arc(str(tmp_path / "arc.db"), dry_run=True)
    # L1: root committed, asset resolves before wipe
    assert len(out["root_before"]) == 64
    assert out["asset_not_orphaned"] is True
    # L2: same store = same being across a fresh box
    assert out["same_being"] is True
    assert out["identity_a"] == out["identity_b"]
    # L3: Learner ran (0 is acceptable if no patterns yet; must not error)
    assert "learn_created" in out
    # L4: query ledger recorded earnings
    assert out["query_ledger"]["earned_wei"] > 0
    # L5: regret urgency is nonzero after a regret was written
    assert out["regret_urgency"] > 0.0
    # L6: temporal consolidation is exercised in the canonical arc
    assert out["consolidated"] == 0
    assert out["consolidation_retained"] >= 1
    assert out["archive_recoverable"] == 0
    # policy: with memory -> de-risk floor
    assert out["book_with_memory_equity"] <= 0.05
    # wipe: asset orphaned, new identity, back to naive
    assert out["asset_orphaned_after_wipe"] is True
    assert out["same_being_after_wipe"] is False
    assert out["book_without_memory_equity"] == 0.55


def test_spine_second_act_runs_live(tmp_path):
    """The full 16-layer arc: L9-L16 execute on the live store before the wipe,
    each beat deterministic and load-bearing."""
    out = run_arc(str(tmp_path / "arc2.db"), dry_run=True)
    # L9: the gate rejects noise and persists a rich lesson
    assert out["l9_noise_rejected"] is True
    assert out["l9_rich_persisted"] is True
    # L10: knows what it knows (COVERED) and flags what it doesn't (UNKNOWN)
    assert out["l10_known"] in ("COVERED", "THIN")
    assert out["l10_unknown"] == "UNKNOWN"
    assert out["l10_confidence"] > 0.5
    # L11: guard vetoes the naive 0.55 book under stress
    assert out["l11_guards_naive"] is True
    # L12: a store that never lived the crisis imports + de-risks
    assert out["l12_imported"] is True
    assert out["l12_buyer_derisks"] is True
    # L13: high-confidence belief wins over the low-confidence dissenter
    assert out["l13_consensus"] == "CONVERGED"
    # L14: the UNKNOWN topic is scheduled into the curriculum
    assert out["l14_plans_unknown"] == "unexplored alien-trading topic"
    # L15: scar tissue distills into a rule that generalizes to a novel frame
    assert out["l15_rule_learned"] is True
    assert out["l15_generalizes"] is True
    # L16: refuses the silent wipe, then wipes only under an explicit, audited
    # force — leaving the asset orphaned and identity changed (the beat lives on)
    assert out["l16_refuses"] is True
    assert out["l16_wiped"] is True
    assert out["wipe_audit"] is True
