"""Tests for the benchmark-alignment enhancements (graph / scale / audit).

(a) Relational board — typed edges in Sibyl's native entity_relations table.
(b) Scale stress — large corpus, exact recall with timing.
(c) Audit chain — tamper-evident journal seal (edit/insert/delete all break it).
"""

from __future__ import annotations

import sqlite3

import pytest

from dejavu.graph_audit import (graph_impact, graph_neighbors, link_entities,
                                seal_journal, seed_corpus, scale_recall_check,
                                verify_journal)
from dejavu.memory import Memory

TENANT = "fleet-brain"


@pytest.fixture()
def mem(tmp_path):
    m = Memory(str(tmp_path / "ga.db"), tenant_id=TENANT)
    yield m
    m.close()


# ---------------------------------------------------------------------------
# (a) relational board
# ---------------------------------------------------------------------------

def test_link_and_traverse(mem):
    mem.set_entity("company", "acme", {"sector": "credit"}, status="active")
    mem.set_entity("view", "news/market", {"headline": "acme spreads"},
                   status="active")
    assert link_entities(mem, "view", "news/market", "company", "acme",
                         "impacts", {"weight": 0.8})
    nb = graph_neighbors(mem, "view", "news/market", direction="out")
    assert {"category": "company", "name": "acme",
            "relation": "impacts"} in nb


def test_link_idempotent(mem):
    mem.set_entity("company", "a", {}, status="active")
    mem.set_entity("company", "b", {}, status="active")
    assert link_entities(mem, "company", "a", "company", "b", "peer")
    assert link_entities(mem, "company", "a", "company", "b", "peer")
    with mem.client.storage.transaction() as conn:
        n = conn.execute("SELECT COUNT(*) FROM entity_relations "
                         "WHERE tenant_id=?", (TENANT,)).fetchone()[0]
    assert n == 1


def test_link_missing_endpoint_is_false(mem):
    assert not link_entities(mem, "company", "ghost", "company", "acme", "x")


def test_graph_impact_two_hops(mem):
    """stress view -> company -> sector view surfaces in two hops."""
    mem.set_entity("view", "news/market", {"headline": "spreads blow out"},
                   status="active")
    mem.set_entity("company", "acme", {"sector": "credit"}, status="active")
    mem.set_entity("view", "sector/credit",
                   {"headline": "credit sector stress"}, status="active")
    link_entities(mem, "view", "news/market", "company", "acme", "impacts")
    link_entities(mem, "company", "acme", "view", "sector/credit", "exposes")
    impact = graph_impact(mem, "view", "news/market", hops=2)
    names = {(h["category"], h["name"]) for h in impact}
    assert ("company", "acme") in names
    assert ("view", "sector/credit") in names


# ---------------------------------------------------------------------------
# (b) scale stress
# ---------------------------------------------------------------------------

def test_seed_corpus_scale_and_recall(mem):
    stats = seed_corpus(mem, n_companies=30, n_views=120, n_events=60)
    assert stats["companies"] + stats["views"] + stats["events"] == 210
    # needle recall stays exact at scale
    rc = scale_recall_check(mem, trials=5)
    assert rc["needle_top1"] is True
    assert rc["top1_rate"] == 1.0
    assert rc["median_ms"] is not None


# ---------------------------------------------------------------------------
# (c) audit chain
# ---------------------------------------------------------------------------

def test_seal_and_verify_clean(mem):
    for i in range(12):
        mem.write_event(evaluated={"i": i}, acted={"op": "record"})
    seal = seal_journal(mem)
    assert seal["rows"] == 12
    assert len(seal["digest"]) == 64
    v = verify_journal(mem)
    assert v["ok"] is True and v["digest_match"] is True


def test_tamper_edit_breaks_chain(mem, tmp_path):
    for i in range(5):
        mem.write_event(evaluated={"i": i}, acted={"op": "record"})
    seal_journal(mem)
    mem.close()
    db = str(tmp_path / "ga.db")
    con = sqlite3.connect(db)
    con.execute("UPDATE journal_events SET acted='{\"tampered\":1}' "
                "WHERE id=(SELECT id FROM journal_events LIMIT 1)")
    con.commit()
    con.close()
    m2 = Memory(db, tenant_id=TENANT)
    assert verify_journal(m2)["ok"] is False
    m2.close()


def test_tamper_delete_breaks_chain(mem, tmp_path):
    for i in range(5):
        mem.write_event(evaluated={"i": i}, acted={"op": "record"})
    seal_journal(mem)
    mem.close()
    db = str(tmp_path / "ga.db")
    con = sqlite3.connect(db)
    con.execute("DELETE FROM journal_events "
                "WHERE id=(SELECT id FROM journal_events LIMIT 1)")
    con.commit()
    con.close()
    m2 = Memory(db, tenant_id=TENANT)
    v = verify_journal(m2)
    assert v["ok"] is False and v["rows"] != v["sealed_rows"]
    m2.close()


def test_verify_without_seal(mem):
    v = verify_journal(mem)
    assert v["ok"] is False and "seal" in v["reason"]
