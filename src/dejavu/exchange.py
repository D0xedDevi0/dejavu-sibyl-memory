"""L12 — EXCHANGE: memory that travels between agents.

Every memory product treats a store as a walled garden: what one agent learns
dies with it (or, at best, is copied into another agent's prompt by hand, with
no provenance and no gate). THE SPINE's L12 makes a hard-won lesson a
**portable, verifiable, priced artifact** — the same "scar tissue" that L1
mints onchain and L4 sells via the live x402 endpoint can now be:

    export_lesson()  -> a buyer-facing artifact: the lesson body + its recorded
                         provenance + a deterministic content hash + a price.
                         The hash lets ANY store verify the artifact is intact
                         and unmodified.
    verify_artifact() -> recompute the hash; true iff the artifact is exactly
                         as the exporting store produced it.
    import_lesson()  -> verify, then route the foreign lesson through the L9
                         DISCERNMENT gate (foreign memory is gated like local
                         memory — a polluted artifact gets refused), record its
                         provenance with the ORIGIN store as source, journal the
                         purchase, and optionally credit the seller's earnings
                         ledger (the x402 settlement side).

The load-bearing result is cross-agent transfer: a buyer store that NEVER lived
the crisis imports the seller's lesson, and `decide_differently` on a fresh
session now cold-starts into the de-risked book. One agent's scar tissue is
another agent's instant, verified, gated education — purchased, not scraped.

Deterministic. Verification needs no network — the hash is self-contained.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from .gates import gate_write
from .meta import _unwrap_body, content_hash, record_provenance

ARTIFACT_SCHEMA = "dejavu/memory-lesson/1"
DEFAULT_PRICE_WEI = 1_000_000_000  # $0.01-ish read (mirrors the live x402 quote)


def _hashable(artifact_body: dict, prov: dict, category: str, name: str) -> str:
    return content_hash({
        "schema": ARTIFACT_SCHEMA, "category": category, "name": name,
        "body": artifact_body, "provenance": prov,
    })


def export_lesson(memory, name: str, *,
                  price_wei: int = DEFAULT_PRICE_WEI) -> dict:
    """Package one live lesson (+ its provenance) into a portable artifact.

    The content hash covers body + provenance + identity ONLY (not the price or
    timestamp), so the same lesson exports to an identical, verifiable artifact
    every time — two stores can compare digests and agree on what 'this lesson
    is' without trusting each other.
    """
    ent = memory.get_entity("lesson", name)
    body = ent["body"]
    category = "lesson"
    prov = _unwrap_body(memory.get_reference(f"meta/prov/{category}::{name}"))
    h = _hashable(body, prov, category, name)
    return {
        "schema": ARTIFACT_SCHEMA,
        "category": category,
        "name": name,
        "body": body,
        "provenance": prov,
        "owner": memory.tenant_id,
        "price_wei": int(price_wei),
        "content_hash": h,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def verify_artifact(artifact: dict) -> dict:
    """Recompute the content hash and confirm the artifact is intact. Returns
    {valid: bool, reason: str} — never a bare True/False (no silent failure)."""
    try:
        if artifact.get("schema") != ARTIFACT_SCHEMA:
            return {"valid": False, "reason": "unrecognized schema"}
        body = artifact.get("body")
        if not isinstance(body, dict):
            return {"valid": False, "reason": "malformed body"}
        h = _hashable(body, artifact.get("provenance") or {},
                      artifact.get("category", "lesson"),
                      artifact.get("name", ""))
        if h != artifact.get("content_hash"):
            return {"valid": False, "reason": "content hash mismatch (tampered)"}
        return {"valid": True, "reason": "intact and verified"}
    except Exception as e:  # pragma: no cover
        return {"valid": False, "reason": f"verification error: {e}"}


def import_lesson(memory, artifact: dict, *,
                  cap: int | None = None,
                  credit_seller: Any = None) -> dict:
    """Verify + gate a foreign lesson into THIS store.

    - verify_artifact first (a tampered/noise artifact is refused outright).
    - then route through L9 `gate_write` so foreign memory earns its slot like
      local memory (a low-information artifact hits the noise floor and is
      REJECTed — this is foreign-ingestion discernment).
    - record provenance with the ORIGIN store as `source` (so `confidence`
      knows where the knowledge came from and can downgrade it accordingly),
      and preserve the `hard` flag so imported scar tissue feeds L11 GUARD.
    - journal the purchase and, if `credit_seller` is given, credit that
      store's earnings ledger (the x402 settlement leg).
    """
    v = verify_artifact(artifact)
    if not v["valid"]:
        return {"verdict": "reject", "reason": v["reason"], "gate_action": None,
                "content_hash": artifact.get("content_hash")}

    category = artifact.get("category", "lesson")
    name = artifact.get("name", "")
    body = artifact.get("body")
    prov = artifact.get("provenance") or {}
    owner = artifact.get("owner", "unknown")
    price = int(artifact.get("price_wei", DEFAULT_PRICE_WEI))

    dec = gate_write(
        memory, category, name, cast(dict, body),
        source=prov.get("source") or owner,
        evidence=int(prov.get("evidence", 0)),
        falsifiable=bool(prov.get("falsifiable")), cap=cap,
    )

    if dec.action == "REJECT":
        memory.write_event(
            evaluated={"category": category, "name": name, "from": owner},
            acted={"action": "IMPORT_REJECTED", "gate": dec.reason},
            forward="foreign memory refused by the L9 gate",
            extra={"content_hash": artifact.get("content_hash"),
                   "price_wei": price})
        return {"verdict": "reject", "reason": f"gate: {dec.reason}",
                "gate_action": dec.action,
                "content_hash": artifact.get("content_hash")}

    # Ground provenance + preserve the hard flag for L11.
    record_provenance(memory, category, name,
                      source=owner, evidence=int(prov.get("evidence", 0)),
                      falsifiable=bool(prov.get("falsifiable")),
                      hard=bool(prov.get("hard")))

    # Purchase receipt on the buyer store.
    memory.write_event(
        evaluated={"category": category, "name": name, "from": owner},
        acted={"action": "IMPORTED", "gate": dec.action, "price_wei": price},
        forward=f"imported {owner}'s verified lesson via L12 exchange",
        extra={"content_hash": artifact.get("content_hash"),
               "verified": v["valid"]})

    # Optional: credit the seller's earnings ledger (x402 settlement analog).
    if credit_seller is not None:
        from .sovereign import record_payment
        record_payment(credit_seller, "lesson", name, price)

    return {"verdict": "imported", "reason": "verified + gated + provenance "
            f"recorded (source={owner})", "gate_action": dec.action,
            "content_hash": artifact.get("content_hash"),
            "price_wei": price}
