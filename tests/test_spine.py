"""Tests for the fused Sovereign Memory spine (five layers, one arc)."""

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
    # policy: with memory -> de-risk floor
    assert out["book_with_memory_equity"] <= 0.05
    # wipe: asset orphaned, new identity, back to naive
    assert out["asset_orphaned_after_wipe"] is True
    assert out["same_being_after_wipe"] is False
    assert out["book_without_memory_equity"] == 0.55
