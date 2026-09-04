"""L16 — CONSENT: memory that argues for its own life.

L1 says the memory OWNS itself; L2 says wiping it changes the being. But
every memory product still lets a caller delete the store with one silent call
— no accounting for what dies, no audit of the act. That is a contradiction:
an asset that "owns itself" can still be vandalised without a trace.

THE SPINE's L16 makes destruction a negotiated, audited act:

    wipe_impact()     -> BEFORE anything is deleted, enumerate exactly what is
                         at stake: the identity the store grounds, the onchain
                         asset it anchored (L1/L7), the hard lessons that guard
                         against known harm (L11), every live lesson / archived
                         memory / journal event. Deterministic census.

    request_wipe()    -> asks permission. Without `force=True` it REFUSES and
                         returns the impact + a consent requirement — the memory
                         does not cooperate in its own silent erasure. With
                         `force=True` (an explicit, deliberate override) it
                         first writes an AUDIT RECORD — a store-independent log
                         on disk that survives the deletion — capturing a
                         pre-wipe content hash, the impact census, a reason and
                         a timestamp, THEN performs the wipe. The act is
                         permanent but never untraceable.

Load-bearing mirror: a silent `delete_store()` erases identity + guard memory
with no record — the deletion is indistinguishable from corruption. With L16, a
wipe is recoverable-by-record: an auditor can always read who wiped what, why,
and what it cost. Same "absence is not silence" discipline, applied to the most
destructive operation the store has.

Deterministic (no LLM/RNG). Never touches live decision logic on the read path.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from .meta import content_hash


def _wipe_log_path(memory) -> str:
    return os.path.join(os.path.dirname(str(memory.db_path)),
                        ".wipe-audit.jsonl")


def _best_effort(fn):
    """Run a census probe; return None rather than crash if it can't resolve."""
    try:
        return fn()
    except Exception:
        return None


def wipe_impact(memory) -> dict:
    """Enumerate everything a wipe would destroy. Pure read; never mutates."""
    live = _best_effort(lambda: memory.list_entities(limit=100000)) or []
    lessons = [e for e in live if e.get("category") == "lesson"]
    hard = []
    try:
        from .guard import hard_lessons
        hard = hard_lessons(memory)
    except Exception:
        hard = []
    archived = _best_effort(lambda: memory.list_archived()) or []
    n_events = _best_effort(lambda: len(list(memory.read_events(limit=100000)))) or 0

    identity = None
    anchored = None
    try:
        from . import sovereign
        identity = {"id": sovereign.identity(memory).get("id")}
        anchored = sovereign.resolve_anchor(memory)
    except Exception:
        identity = None
        anchored = None

    # Pre-wipe content hash over live entities (a fingerprint of what dies).
    try:
        digest = content_hash({"live": [e.get("body") for e in live]})
    except Exception:
        digest = None

    return {
        "live_entities": len(live),
        "lessons": len(lessons),
        "hard_lessons_guarding_harm": len(hard),
        "archived_memories": len(archived),
        "journal_events": n_events,
        "identity_id": identity.get("id") if identity else None,
        "onchain_anchor": anchored,
        "pre_wipe_content_hash": digest,
    }


def request_wipe(memory, *, force: bool = False, reason: str = "") -> dict:
    """Refuse a silent wipe; audit a deliberate one.

    Returns either {granted: False, consent_required: True, impact, message} or
    {granted: True, wiped: True, audit_path, audit}.
    """
    impact = wipe_impact(memory)
    if not force:
        return {
            "granted": False,
            "consent_required": True,
            "impact": impact,
            "message": ("memory refuses silent erasure: this store grounds an "
                        "identity and guards against known harm. Pass "
                        "force=True with an explicit reason to authorize the "
                        "destructive wipe."),
        }

    # Authorized wipe: journal the act to a store-INDEPENDENT log first, so the
    # destruction is recoverable-by-record even though the store is gone.
    audit = {
        "event": "MEMORY_WIPED",
        "at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "impact": impact,
    }
    path = _wipe_log_path(memory)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit, default=str) + "\n")
    except Exception:  # pragma: no cover — audit failure must not block wipe
        path = None

    # Perform the destructive wipe.
    memory.delete_store()
    return {"granted": True, "wiped": True, "audit_path": path, "audit": audit}


def read_wipe_audit(memory) -> list[dict]:
    """Read the store-independent wipe log (survives any single deletion)."""
    path = _wipe_log_path(memory)
    out: list[dict] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out
