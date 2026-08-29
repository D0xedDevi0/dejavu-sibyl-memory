"""Temporal memory + strategic forgetting — the memory is a *dynamic* data layer.

THE SPINE layers so far treat memory as an ownable, self-authoring asset (what
it IS). This layer treats memory as a *living, time-bound* record (what it
REMEMBERS, and for how long):

  - TIMELINE: every lesson carries a `last_reinforced_at` so the agent knows
    WHEN it last believed/used a fact (not just that it exists).
  - POINT-IN-TIME RECALL: `recall_asof` answers "what did I believe on date X?"
    — the memory supports temporal (as-of) queries like a real data layer.
  - STRATEGIC FORGETTING: `consolidate` moves stale lessons (not reinforced
    within `max_age_days`) into the ARCH tier. This is the deliberate,
    auditable counterpart to "forgetting is a bug": the agent forgets ON
    PURPOSE, keeps the live store lean, and can still reconstruct the past
    from the archive. The wipe that matters (full store delete) still orphans
    the onchain asset and resets identity — consolidation does NOT touch the
    sovereign layer.

This is deterministic (no LLM), fully testable, and reuses the existing ARCH
tier (`archive_entity` / `list_archived`).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .memory import Memory

_REINFORCE_KEY = "last_reinforced_at"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def touch_lesson(mem: Memory, name: str, *, lesson: str | None = None,
                 note: str = "") -> dict:
    """Mark a lesson as reinforced "now". Reinforcement = the agent used/relied
    on this memory again, which resets its staleness clock. Returns the body."""
    existing = mem.get_lesson(name)
    body: dict = {}
    if isinstance(existing, dict) and isinstance(existing.get("body"), dict):
        body = dict(existing["body"])
    if lesson:
        body["lesson"] = lesson
    elif "lesson" not in body:
        body["lesson"] = name
    if note:
        body["note"] = note
    body[_REINFORCE_KEY] = _now_iso()
    entity = mem.set_entity("lesson", name, body)
    return {"name": name, "reinforced_at": body[_REINFORCE_KEY], "entity": entity}


def _parse_ts(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def lesson_reinforced_at(mem: Memory, name: str) -> datetime | None:
    """When was this lesson last reinforced (or written)? None if unknown."""
    ent = mem.get_lesson(name)
    if isinstance(ent, dict):
        body = ent.get("body")
        if isinstance(body, dict) and isinstance(body.get(_REINFORCE_KEY), str):
            ts = _parse_ts(body[_REINFORCE_KEY])
            if ts is not None:
                return ts
    return None


def recall_asof(mem: Memory, queries: list[str], asof: str, *,
                limit: int = 20) -> list[dict]:
    """Point-in-time recall: only lessons that were known (reinforced/written)
    on or before `asof` are returned. Filters the normal recall by timestamp.

    Returns [{name, lesson, known_at}]. This is the temporal-as-of query — the
    memory answers "what did I believe then?" like a versioned data layer.
    """
    asof_dt = _parse_ts(asof)
    if asof_dt is None:
        raise ValueError(f"asof must be an ISO datetime, got {asof!r}")

    out: list[dict] = []
    seen: set[str] = set()
    for q in queries:
        for hit in mem.search(q, limit=limit):
            name = hit.get("name") or hit.get("key")
            body = hit.get("body")
            if isinstance(body, dict):
                lesson = body.get("lesson")
            else:
                lesson = body if isinstance(body, str) else None
            if not lesson or lesson in seen:
                continue
            # when was it known? latest reinforce/write.
            known = None
            if name:
                ts = lesson_reinforced_at(mem, name)
                if ts is not None:
                    known = ts
            if known is None:
                # fall back to the search hit's ts
                parsed = _parse_ts(hit.get("ts"))
                if parsed is not None:
                    known = parsed
            if known is None or known <= asof_dt:
                seen.add(lesson)
                out.append({"name": name, "lesson": lesson,
                            "known_at": known.isoformat() if known else None})
    return out


def _staleness_days(known: datetime, now: datetime) -> float:
    return (now - known).total_seconds() / 86400.0


def consolidate(mem: Memory, *, max_age_days: float, now: datetime | None = None,
                dry_run: bool = False) -> dict:
    """Strategic forgetting: move lessons not reinforced within max_age_days to
    the ARCH tier (soft-forget). Keeps the live store lean and auditable.

    Returns a report of what was archived (and would-be-archived in dry_run).
    Does NOT touch the sovereign/identity layers — full-store wipe still
    orphans the onchain asset; this is deliberate, scoped forgetting.
    """
    now = now or datetime.now(timezone.utc)
    lessons = mem.list_lessons(status="active", limit=1000)
    archived: list[dict] = []
    retained: list[dict] = []
    for ent in lessons:
        name = ent.get("name") or ent.get("key")
        if not name:
            continue
        known = lesson_reinforced_at(mem, name) if name else None
        if known is None:
            # no timestamp -> treat as fresh (don't forget what we can't date)
            retained.append({"name": name, "staleness_days": 0.0})
            continue
        age = _staleness_days(known, now)
        item = {"name": name, "staleness_days": round(age, 3),
                "last_reinforced_at": known.isoformat()}
        if age > max_age_days:
            if not dry_run:
                mem.archive_entity("lesson", name, reason="staleness")
            archived.append(item)
        else:
            retained.append(item)

    report = {
        "max_age_days": max_age_days,
        "dry_run": dry_run,
        "scanned": len(lessons),
        "archived": len(archived),
        "retained": len(retained),
        "archived_list": archived,
    }
    return report


def reconstruct_past(mem: Memory, *, limit: int = 500) -> list[dict]:
    """Read the ARCH tier back — the memory reconstructs what it used to know.
    This proves consolidation is NOT destructive: the past is recoverable from
    the archive, while the live store stays lean."""
    return mem.list_archived(category="lesson")
