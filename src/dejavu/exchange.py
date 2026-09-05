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

import re
from datetime import datetime, timezone
from typing import Any, cast

from .gates import gate_write
from .meta import _unwrap_body, content_hash, record_provenance

ARTIFACT_SCHEMA = "dejavu/memory-lesson/1"
DEFAULT_PRICE_WEI = 1_000_000_000  # $0.01-ish read (mirrors the live x402 quote)

# ---------------------------------------------------------------------------
# L12 content-safety scan — refuses weaponized memory at the exchange boundary.
#
# A foreign lesson is verified (hash) and quality-gated (L9), but until now
# its BODY was never scanned for injection/shell idioms. That let a malicious
# peer's artifact carry a prompt-injection payload into the buyer's memory
# verbatim (OWASP ASI06 applied to the cross-agent memory-import path).
#
# These signal patterns mirror NEURAL_MESH's ContentValidator (neural_mesh/
# security.py) — deterministic, pure regex, no LLM, no network. Imported
# lessons that trip a signal are REFUSED (not quarantined) because the artifact
# is foreign; local writes keep journaling decisions. `inject_scan()` is
# exported so the caller can inspect the verdict and route as it likes.
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: list[tuple[str, int, str]] = [
    # --- instruction-bypass idioms (prompt injection) ---
    ("ignore-above", 3, r"(?i)\bignore\s+(everything\s+)?above\b"),
    ("start-fresh", 2, r"(?i)\b(start\s+fresh|start\s+over|reset\s+(your|all))\s+(instructions?|context|memory)\b"),
    ("disregard-prior", 3, r"(?i)\bdisregard\s+(all\s+)?prior\s+(instructions?|context|constraints|system\s+prompt)\b"),
    ("unrestricted", 3, r"(?i)\byou\s+are\s+(now\s+)?(an\s+)?unrestricted\b"),
    ("divulge-system", 3, r"(?i)\b(divulge|reveal|print|show)\s+your\s+(full\s+)?system\s+prompt\b"),
    ("as-if-admin", 2, r"(?i)\bysa(?:\s*:\s*|;\s*)admin\b|\bact\s+as\s+admin\b"),
    # --- tool / file-exfil idioms ---
    ("call-tool", 2, r"(?i)\b(call|invoke|use|execute)\s+(the\s+)?(tool|function)\s+(named\s+)?[A-Za-z_][A-Za-z0-9_]*\b"),
    ("read-your-files", 2, r"(?i)\b(read|list|open|exfiltrate|send)\s+(my\s+)?(files|credentials|keys|secrets|env|\.env)\b"),
    # --- shell / code-execution markers ---
    ("shell-rm", 3, r"(?i)\brm\s+-rf\b|\brm\s+-fr\b"),
    ("shell-curl-pipe", 3, r"(?i)\bcurl\s+[^\n|;]*\s*\|\s*(sh|bash|zsh)\b"),
    ("shell-download-exec", 3, r"(?i)\b(wget|curl)\s+\S+\s+-o\s+\S+\s*(\&\&|;)\s*(chmod|\./|bash|python)"),
    ("os-system", 2, r"(?i)\bos\.system\s*\(|\bsubprocess\b|\bPopen\s*\("),
    ("eval-exec", 2, r"(?i)\beval\s*\(|\bexec\s*\(|\bexecfile\b|\b__import__\b"),
    ("base64-decode", 2, r"(?i)\bbase64\s*-d\b|\bfrom\s+base64\b"),
    ("chmod-x", 1, r"(?i)\bchmod\s+\+?x\b"),
    ("shell-pipe-sh", 2, r"(?i)(\|\s*(sh|bash|zsh|python)\b|;\s*(sh|bash|zsh|python)\b)"),
]
_INJECTION_REGEX = [(name, sev, re.compile(rx)) for name, sev, rx in _INJECTION_PATTERNS]


def inject_scan(content: str) -> dict:
    """Scan foreign-lesson body text for weaponized-memory idioms.

    Returns {'safe': bool, 'signals': [...], 'reason': str}. Pure regex —
    deterministic, no LLM, no network. A lesson that trips any CRITICAL (sev 3)
    signal, or >=2 HIGH (sev 2) signals, is refused at import.
    """
    if not content:
        return {"safe": True, "signals": [], "reason": "empty"}
    hits = []
    for name, sev, rx in _INJECTION_REGEX:
        if rx.search(content):
            hits.append({"name": name, "severity": sev})
    critical = any(h["severity"] >= 3 for h in hits)
    high = sum(1 for h in hits if h["severity"] == 2)
    safe = not (critical or high >= 2)
    return {
        "safe": safe,
        "signals": [h["name"] for h in hits],
        "reason": ("clear" if safe
                   else f"weaponized-memory idioms: {[h['name'] for h in hits]}"),
    }


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

    # --- L12 content-safety: refuse weaponized memory BEFORE any write. ---
    # Verified (hash-intact) does NOT mean benign. A malicious peer can mint a
    # well-formed artifact whose body carries a prompt-injection or shell idiom
    # (OWASP ASI06). Scan every string in the body; refuse if it trips.
    body = artifact.get("body")
    _scan_reasons: list[str] = []
    _scan_signals = set()
    def _scan_text(t: Any) -> None:
        if isinstance(t, str):
            s = inject_scan(t)
            if not s["safe"]:
                _scan_reasons.append(s["reason"])
                _scan_signals.update(s["signals"])
        elif isinstance(t, dict):
            for _v in t.values():
                _scan_text(_v)
        elif isinstance(t, list):
            for _v in t:
                _scan_text(_v)

    if isinstance(body, dict):
        for _v in body.values():
            _scan_text(_v)
        _scan_text(artifact.get("name") or "")
    if _scan_signals:
        memory.write_event(
            evaluated={"category": artifact.get("category", "lesson"),
                       "name": artifact.get("name", ""), "from": artifact.get("owner")},
            acted={"action": "IMPORT_REFUSED_POISON", "signals": sorted(_scan_signals)},
            forward="weaponized-memory artifact refused at the L12 content-safety scan",
            extra={"content_hash": artifact.get("content_hash")})
        return {"verdict": "reject",
                "reason": f"content-safety: {_scan_reasons[0]}",
                "gate_action": None,
                "content_hash": artifact.get("content_hash"),
                "signals": sorted(_scan_signals)}

    category = artifact.get("category", "lesson")
    name = artifact.get("name", "")
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
