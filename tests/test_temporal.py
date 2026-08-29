"""Tests for temporal memory + strategic forgetting (the dynamic data layer)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dejavu.memory import Memory
from dejavu.temporal import (consolidate, lesson_reinforced_at, recall_asof,
                             reconstruct_past, touch_lesson)


@pytest.fixture()
def mem(tmp_path):
    m = Memory(str(tmp_path / "m.db"), tenant_id="temporal-test")
    yield m
    m.close()


def test_touch_lesson_sets_reinforce_timestamp(mem):
    mem.write_lesson("c1", "de-risk on stress", frame={"vix": 52.0})
    res = touch_lesson(mem, "c1", note="reinforced")
    assert res["reinforced_at"]  # ISO string
    ts = lesson_reinforced_at(mem, "c1")
    assert ts is not None
    # recent (within the last minute)
    assert (datetime.now(timezone.utc) - ts) < timedelta(minutes=1)


def test_recall_asof_filters_by_time(mem):
    # write a lesson, reinforce it at a known past time
    mem.write_lesson("old", "credit stress crisis lesson", frame={"vix": 50})
    touch_lesson(mem, "old")
    past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    # as-of 30 days ago, the "old" lesson hadn't been reinforced yet -> filtered out
    hits = recall_asof(mem, ["credit stress crisis lesson"], asof=past)
    assert hits == []
    # as-of now, it's known
    hits_now = recall_asof(mem, ["credit stress crisis lesson"],
                           asof=datetime.now(timezone.utc).isoformat())
    assert any(h["lesson"] == "credit stress crisis lesson" for h in hits_now)


def test_recall_asof_rejects_bad_date(mem):
    with pytest.raises(ValueError):
        recall_asof(mem, ["x"], asof="not-a-date")


def test_consolidate_archives_stale_and_keeps_fresh(mem):
    # a stale lesson reinforced 30 days ago
    mem.write_lesson("stale", "old lesson", frame={"vix": 60})
    ent = mem.get_lesson("stale")
    stale_body = dict(ent["body"])
    stale_body["last_reinforced_at"] = (
        datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    mem.set_entity("lesson", "stale", stale_body)

    # a fresh lesson reinforced now
    mem.write_lesson("fresh", "new lesson", frame={"vix": 14})
    touch_lesson(mem, "fresh")

    now = datetime.now(timezone.utc)
    rep = consolidate(mem, max_age_days=7, now=now)
    assert rep["scanned"] == 2
    assert rep["archived"] == 1
    assert rep["retained"] == 1
    names = [a["name"] for a in rep["archived_list"]]
    assert "stale" in names
    assert "fresh" not in names

    # the stale lesson is now in the ARCH tier (recoverable)
    archived = reconstruct_past(mem)
    assert any(a.get("name") == "stale" for a in archived)


def test_consolidate_dry_run_does_not_archive(mem):
    mem.write_lesson("stale", "old", frame={"vix": 60})
    ent = mem.get_lesson("stale")
    body = dict(ent["body"])
    body["last_reinforced_at"] = (
        datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    mem.set_entity("lesson", "stale", body)

    rep = consolidate(mem, max_age_days=7,
                      now=datetime.now(timezone.utc), dry_run=True)
    assert rep["dry_run"] is True
    assert rep["archived"] == 1  # would archive...
    # ...but did NOT touch the live store
    assert reconstruct_past(mem) == []


def test_full_store_wipe_still_resets(mem):
    # consolidation is scoped; a full wipe still empties everything
    mem.write_lesson("a", "x", frame={"vix": 10})
    assert mem.exists
    mem.delete_store()
    assert not mem.exists
