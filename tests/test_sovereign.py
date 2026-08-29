"""Tests for the Sovereign + Regret memory layers (the upgraded spine).

Sovereign memory:
  (1) content-addressed root is deterministic and content-flipping
  (2) identity = memory (same store = same being; wipe store = new identity)
  (3) sovereign mint commits the root; asset_orphaned after deletion
  (4) query economics: quote + payment ledger

Regret memory:
  (5) write/recall counterfactuals
  (6) regret urgency scales with would-have-lost magnitude
  (7) wiped store -> no regrets -> zero urgency (load-bearing)
"""

from __future__ import annotations

import pytest

from dejavu.config import Config
from dejavu.memory import Memory
from dejavu.regret import (recall_regrets, regret_de_risk_book, regret_urgency,
                           write_regret)
from dejavu.sovereign import (asset_orphaned, identity, is_same_being,
                              ledger_balance, memory_root, quote_query,
                              record_payment, sovereign_mint)

TENANT = "sovereign-test"


@pytest.fixture()
def mem(tmp_path):
    m = Memory(str(tmp_path / "sov.db"), tenant_id=TENANT)
    yield m
    m.close()


# ---------------------------------------------------------------------------
# (1) content-addressed root
# ---------------------------------------------------------------------------

def test_root_deterministic(mem):
    mem.write_lesson("l1", "de-risk when credit stress spikes",
                     frame={"vix": 52})
    r1 = memory_root(mem)
    r2 = memory_root(mem)
    assert r1["root"] == r2["root"]
    assert len(r1["root"]) == 64


def test_root_flips_on_content_change(mem):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    before = memory_root(mem)["root"]
    mem.write_lesson("l2", "hedge before earnings")
    after = memory_root(mem)["root"]
    assert before != after


# ---------------------------------------------------------------------------
# (2) identity = memory
# ---------------------------------------------------------------------------

def test_identity_same_store_same_being(mem, tmp_path):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    a = identity(mem)
    m2 = Memory(str(tmp_path / "copy.db"), tenant_id=TENANT)
    m2.write_lesson("l1", "de-risk when credit stress spikes")
    b = identity(m2)
    assert is_same_being(a, b)
    m2.close()


def test_wipe_store_changes_identity(mem):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    before = identity(mem)["id_sha256"]
    mem.delete_store()
    # fresh store (empty) -> different identity
    m2 = Memory(mem.db_path, tenant_id=TENANT)
    after = identity(m2)["id_sha256"]
    assert before != after
    m2.close()


# ---------------------------------------------------------------------------
# (3) sovereign mint + economic deletion gate
# ---------------------------------------------------------------------------

def test_mint_dry_run_commits_root(mem):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    cfg = Config(dry_run=True)
    mint = sovereign_mint(mem, cfg)
    assert mint.dry_run is True
    assert mint.root == memory_root(mem)["root"]
    assert mint.identity_id == identity(mem)["id"]
    assert mint.tx_hash is None


def test_asset_orphaned_after_deletion(mem):
    mem.write_lesson("l1", "de-risk when credit stress spikes")
    cfg = Config(dry_run=True)
    mint = sovereign_mint(mem, cfg)
    assert asset_orphaned(mem, mint) is False  # still resolves
    mem.delete_store()
    m2 = Memory(mem.db_path, tenant_id=TENANT)
    assert asset_orphaned(m2, mint) is True    # committed asset now orphaned
    m2.close()


# ---------------------------------------------------------------------------
# (4) query economics
# ---------------------------------------------------------------------------

def test_query_quote_and_ledger(mem):
    mem.set_entity("view", "news/market", {"headline": "spreads"}, status="active")
    q = quote_query(mem, "view", "news/market", price_wei=500)
    assert q.price_wei == 500
    assert ledger_balance(mem) == {"paid_queries": 0, "earned_wei": 0}
    rec = record_payment(mem, "view", "news/market", q.price_wei)
    assert rec["paid_queries"] == 1
    assert rec["earned_wei"] == 500
    assert ledger_balance(mem)["earned_wei"] == 500


# ---------------------------------------------------------------------------
# (5) regret memory: write / recall
# ---------------------------------------------------------------------------

def test_write_and_recall_regret(mem):
    write_regret(mem, "crisis-1", taken="de-risked to cash",
                 road_not_taken="stayed overweight equity", would_have_lost=18.0)
    regrets = recall_regrets(mem, ["road not taken would have lost"])
    assert len(regrets) == 1
    assert "would have lost 18.0%" in regrets[0]


# ---------------------------------------------------------------------------
# (6) regret urgency
# ---------------------------------------------------------------------------

def test_regret_urgency_scales(mem):
    write_regret(mem, "r1", taken="de-risk", road_not_taken="stayed long",
                 would_have_lost=15.0)
    u = regret_urgency(mem, ["road not taken would have lost"])
    assert 0.0 < u <= 1.0
    assert u == pytest.approx(15.0 / 30.0)


def test_regret_de_risk_book(mem):
    write_regret(mem, "r1", taken="de-risk", road_not_taken="stayed long",
                 would_have_lost=30.0)
    book = regret_de_risk_book(mem, n_regrets=1,
                               urgency=regret_urgency(mem, ["road not taken"]))
    assert book["equity"] == pytest.approx(0.0)  # max urgency -> full cash
    assert book["n_regrets"] == 1


# ---------------------------------------------------------------------------
# (7) wiped store -> no regrets -> zero urgency (load-bearing)
# ---------------------------------------------------------------------------

def test_regret_urgency_zero_when_wiped(mem):
    write_regret(mem, "r1", taken="de-risk", road_not_taken="stayed long",
                 would_have_lost=30.0)
    mem.delete_store()
    m2 = Memory(mem.db_path, tenant_id=TENANT)
    assert regret_urgency(m2, ["road not taken would have lost"]) == 0.0
    assert recall_regrets(m2, ["road not taken would have lost"]) == []
    m2.close()
