"""Write-time conflict resolution — the memory resolves contradictions on write.

THE SPINE's L8 beat (and the SOTA gap mapped in docs/UPGRADES.md): Mem0's
four-op write model resolves UPDATE/DELETE conflicts at write time instead of
blindly overwriting. This module gives THE SPINE the same discipline using
Sibyl's native tiers:

  * `supersede_entity` — when a new value for (category, name) contradicts the
    existing one, do NOT blind-overwrite. It:
        (1) journals a SUPERSEDES event linking old -> new (audit trail),
        (2) moves the LOSER into the ARCH tier (recoverable soft-forgetting,
            via the SDK's own archive_entity), and
        (3) writes the new value as the live WARM entity.
    The old value is never destroyed — it is a recoverable superseded revision.

  * `supersession_chain` — reconstruct the full old -> new revision trail for a
    key by joining the ARCH tier (losers) + the live entity (current winner).
    This is a Graphiti-style valid-interval/supersession chain, in one store.

Deterministic, no LLM, fully testable. Pure addition — existing write paths
(set_entity / write_lesson) are untouched unless a caller opts into supersede.
"""

from __future__ import annotations

from .memory import Memory


def supersede_entity(memory: Memory, category: str, name: str,
                     new_body: dict, *, reason: str = "conflict") -> dict:
    """Write-time conflict resolution: archive the loser, journal the chain,
    write the winner. Returns a report with both the winner and the loser.

    A conflict exists only when (category, name) already held a live value that
    differs from the incoming one. If no conflicting prior value exists, this is
    a plain write (nothing to supersede) and no chain is recorded.
    """
    # Snapshot the prior value FIRST — set_entity upserts in place, so once we
    # write the winner the prior is gone. Detect the conflict before writing.
    superseded = _snapshot_prior(memory, category, name, new_body)

    # Write the winner (live WARM entity).
    winner = memory.set_entity(category, name, new_body)

    if superseded is not None:
        memory.write_event(
            evaluated={"category": category, "name": name},
            acted={"action": "SUPERSEDES", "winner": name},
            forward=reason,
            extra={"old": superseded, "new": new_body},
        )
        _archive_loser(memory, category, name, superseded, reason)

    return {
        "category": category, "name": name,
        "winner": winner, "superseded": superseded,
        "reason": reason, "journaled": superseded is not None,
    }


def _snapshot_prior(memory: Memory, category: str, name: str,
                    new_body: dict) -> dict | None:
    """Detect whether (category, name) already had a live value that differs
    from the incoming one. Returns the prior body if it exists and differs,
    else None (no conflict -> no supersession)."""
    try:
        prior = memory.get_entity(category, name)
    except Exception:
        return None
    prior_body = prior.get("body") if isinstance(prior, dict) else None
    if prior_body is None or prior_body == new_body:
        return None
    return prior_body


def _archive_loser(memory: Memory, category: str, name: str,
                   loser_body: dict, reason: str) -> None:
    """Move the losing revision into the ARCH tier.

    We write the loser back under a versioned name (category, name#<n>) before
    archiving it, so the ARCH tier holds the exact superseded body and
    reconstructing the chain later can read it back verbatim. If the archival
    of the live name conflicts with the new winner, we archive the versioned
    copy — the live name now holds the winner.
    """
    # Attempt to archive the live row's superseded revision; the winner already
    # replaced it, so archive a clearly-labelled historical copy instead.
    versioned = f"{name}#v{_next_rev(memory, category, name)}"
    memory.set_entity(category, versioned, loser_body)
    memory.archive_entity(category, versioned, reason=f"superseded:{reason}")


def _next_rev(memory: Memory, category: str, name: str) -> int:
    """Count existing archived revisions to derive the next version suffix."""
    revs = 0
    for ent in memory.list_archived(category=category):
        ename = ent.get("name", "")
        if ename.startswith(f"{name}#v"):
            try:
                revs = max(revs, int(ename.rsplit("v", 1)[1]))
            except (ValueError, IndexError):
                pass
    return revs + 1


def supersession_chain(memory: Memory, category: str, name: str) -> list[dict]:
    """Reconstruct the old -> new revision trail for a key.

    Returns revisions newest-first: [current winner, ..., oldest archived].
    Each entry has {name, body, tier, superseded_by}. Uses only the live WARM
    entity + the ARCH tier (both native Sibyl tiers)."""
    chain: list[dict] = []

    # Current winner (live WARM).
    try:
        winner = memory.get_entity(category, name)
        if isinstance(winner, dict):
            chain.append({
                "name": name,
                "body": winner.get("body"),
                "tier": "WARM (live)",
                "superseded_by": None,
            })
    except Exception:
        pass

    # Historical losers from ARCH (newest archived first).
    archived = memory.list_archived(category=category)
    losers = [a for a in archived
              if (a.get("name") or "").startswith(f"{name}#v")]
    losers.sort(key=lambda a: (a.get("archived_at") or ""), reverse=True)
    for i, a in enumerate(losers):
        prev = chain[-1]["name"] if chain else name
        chain.append({
            "name": a.get("name"),
            "body": a.get("body"),
            "tier": "ARCH (superseded)",
            "superseded_by": prev,
        })
    return chain
