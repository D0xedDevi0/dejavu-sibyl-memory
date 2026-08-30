"""Tests for THE SPINE L7 (self-referential sovereign loop) and L8 (write-time
conflict resolution / supersession).

L7 — memory that knows it owns itself:
  (1) memory_root folds REFERENCE tier (the anchor changes the fingerprint)
  (2) anchor_self writes the mint receipt back into the store (REFERENCE tier)
  (3) resolve_anchor / is_self_anchored read it back
  (4) a fresh box mounting the same store is still self-anchored (same being)
  (5) wiping the store drops the anchor -> no longer self-anchored

L8 — write-time conflict resolution:
  (6) supersede_entity archives the loser + writes the winner when conflicting
  (7) no conflict -> plain write, no chain journaled
  (8) supersession_chain reconstructs old -> new from ARCH + live WARM
  (9) the loser is recoverable from ARCH (soft forgetting, not destruction)
"""

from __future__ import annotations

import pytest

from dejavu.config import Config
from dejavu.memory import Memory
from dejavu.sovereign import (MintReceipt, anchor_self, identity,
                              is_self_anchored, memory_root, resolve_anchor,
                              sovereign_mint)
from dejavu.supersede import supersede_entity, supersession_chain

TENANT = "sovereign-loop-test"


@pytest.fixture()
def mem(tmp_path):
    m = Memory(str(tmp_path / "loop.db"), tenant_id=TENANT)
    yield m
    m.close()


def _mint(mem: Memory, tmp_path) -> MintReceipt:
    cfg = Config(dry_run=True, wallet_key=tmp_path / "nokey")
    return sovereign_mint(mem, cfg)


# ---------------------------------------------------------------------------
# L7 — self-referential sovereign loop
# ---------------------------------------------------------------------------

def test_root_folds_reference_tier(mem, tmp_path):
    """The anchor changes the content-addressed root -> REFERENCE is part of the
    store's fingerprint, so the memory's identity reflects its own onchain history."""
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    before = memory_root(mem)["root"]
    mint = _mint(mem, tmp_path)
    anchor_self(mem, mint)
    after = memory_root(mem)["root"]
    assert before != after
    assert memory_root(mem)["references"] == 1


def test_anchor_self_and_resolve(mem, tmp_path):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    mint = _mint(mem, tmp_path)
    anchor_self(mem, mint)
    anchor = resolve_anchor(mem)
    assert anchor is not None
    assert anchor["root"] == mint.root
    assert anchor["identity_id"] == mint.identity_id
    assert anchor["tx_hash"] == mint.tx_hash  # None in dry-run


def test_is_self_anchored_matches_mint(mem, tmp_path):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    mint = _mint(mem, tmp_path)
    assert is_self_anchored(mem) is False          # not anchored yet
    anchor_self(mem, mint)
    assert is_self_anchored(mem) is True            # any anchor
    assert is_self_anchored(mem, mint) is True      # matches THIS mint


def test_fresh_box_same_store_still_self_anchored(mem, tmp_path):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    mint = _mint(mem, tmp_path)
    anchor_self(mem, mint)
    ident_a = identity(mem)

    # fresh process mounting the same store -> same being AND still self-anchored
    m2 = Memory(mem.db_path, tenant_id=TENANT)
    assert is_self_anchored(m2, mint) is True
    assert identity(m2)["id_sha256"] == ident_a["id_sha256"]
    m2.close()


def test_wipe_store_drops_anchor(mem, tmp_path):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    mint = _mint(mem, tmp_path)
    anchor_self(mem, mint)
    assert is_self_anchored(mem) is True

    mem.delete_store()
    m2 = Memory(mem.db_path, tenant_id=TENANT)
    # wiped store has no anchor -> it no longer knows it owns the committed root
    assert resolve_anchor(m2) is None
    assert is_self_anchored(m2, mint) is False
    m2.close()


# ---------------------------------------------------------------------------
# L8 — write-time conflict resolution (supersession)
# ---------------------------------------------------------------------------

def test_supersede_archives_loser_and_writes_winner(mem):
    mem.set_entity("lesson", "l1", {"lesson": "stay long in stress", "v": 1})
    report = supersede_entity(
        mem, "lesson", "l1",
        {"lesson": "de-risk to <=5% equity in stress", "v": 2},
        reason="market regime changed",
    )
    assert report["superseded"] == {"lesson": "stay long in stress", "v": 1}
    assert report["journaled"] is True

    # winner is live WARM
    winner = mem.get_entity("lesson", "l1")["body"]
    assert winner["v"] == 2

    # loser is recoverable from ARCH (soft forgetting, not destruction)
    archived = mem.list_archived(category="lesson")
    assert len(archived) >= 1


def test_supersede_no_conflict_is_plain_write(mem):
    report = supersede_entity(
        mem, "lesson", "l1",
        {"lesson": "de-risk when credit stress spikes"},
        reason="first write",
    )
    # no prior conflicting value -> plain write, no chain
    assert report["superseded"] is None
    assert report["journaled"] is False
    assert mem.get_entity("lesson", "l1")["body"]["lesson"] == \
        "de-risk when credit stress spikes"


def test_supersession_chain_reconstructs_trail(mem):
    mem.set_entity("view", "risk/stress", {"credit_stress": 0.3, "v": 1})
    supersede_entity(mem, "view", "risk/stress",
                     {"credit_stress": 1.4, "v": 2}, reason="spreads widen")
    supersede_entity(mem, "view", "risk/stress",
                     {"credit_stress": 2.2, "v": 3}, reason="crisis")

    chain = supersession_chain(mem, "view", "risk/stress")
    # newest-first: live winner first, then archived losers
    assert chain[0]["tier"] == "WARM (live)"
    assert chain[0]["body"]["v"] == 3
    versions = [c["body"]["v"] for c in chain]
    assert 3 in versions and 2 in versions and 1 in versions


def test_supersession_chain_empty_for_new_key(mem):
    assert supersession_chain(mem, "view", "does-not-exist") == []
