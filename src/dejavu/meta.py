"""L10 — META: the memory that knows itself.

Every memory system can answer "what do I remember about X?" Almost none can
answer "what do I NOT know, and how sure am I about what I do know?" Agents
hallucinate coverage: asked about a topic they have zero scar tissue on, they
either bluff a generic answer or silently retrieve a weak near-match and treat
it as knowledge. That is exactly the failure this layer removes.

THE SPINE's L10 gives the store a first-class epistemic mirror:

    snapshot()        -> a census of the store by tier & category (live /
                         archived / reference / events) so the agent always
                         knows its own size and shape.
    coverage()        -> per-category maturity: how much live, decision-bearing
                         memory exists there, and where the blind spots are.
    confidence()      -> per-entity reliability 0..1, from *recorded
                         provenance* (source, corroboration, falsifiability)
                         or a conservative body heuristic. The planner can
                         down-weight weak memory instead of trusting it equally.
    known_unknowns()  -> the anti-hallucination read. Given a query it returns
                         an explicit verdict: COVERED (high-confidence hits),
                         THIN (matches but not trustworthy), or UNKNOWN (no
                         decision-bearing memory). No silent failures — a UNKNOWN
                         is a *signal*, not an empty list: it means "go learn
                         this before acting."

Deterministic (no LLM, no RNG). Provenance is stored as small REFERENCE docs
(`meta/prov/<category>::<name>`) so it survives restarts and never bloats the
entity body.

Load-bearing mirror: with no meta layer, a planner facing an unknown topic
treats absence as "no constraint" and proceeds on the naive path. WITH meta,
`known_unknowns` flags UNKNOWN/THIN and the planner can abstain or de-risk.
Same "absence is not silence" discipline as L8's verdict and L9's gate.
"""

from __future__ import annotations

import hashlib
import json

from .gates import _text_novelty  # deterministic body-richness signal (reused)

_PROV_PREFIX = "meta/prov/"

# Confidence is composed from recorded provenance signals.
W_SOURCE = 0.25        # a named source raises trust
W_CORROB = 0.30        # more corroborating evidence -> higher confidence
W_FALSIF = 0.20        # a falsifiable claim can be checked & corrected
W_SHAPE = 0.25         # body shape: lesson-with-outcome is decision-grade


def _prov_key(category: str, name: str) -> str:
    return f"{_PROV_PREFIX}{category}::{name}"


def record_provenance(memory, category: str, name: str, *,
                      source: str | None = None, evidence: int = 0,
                      falsifiable: bool = False,
                      hard: bool = False) -> None:
    """Persist provenance for an entity so `confidence` is grounded, not guessed.

    Call right after a write (optionally paired with `gated_write`): this is
    what lets META later say *why* a memory is (or is not) trusted. `hard`
    marks a lesson as non-negotiable (feeds L11 GUARD).
    """
    memory.set_reference(_prov_key(category, name), {
        "source": source, "evidence": int(evidence),
        "falsifiable": bool(falsifiable), "hard": bool(hard),
        "recorded": True,
    })


def _get_prov(memory, category: str, name: str) -> dict:
    ref = memory.get_reference(_prov_key(category, name))
    return _unwrap_body(ref)


def _unwrap_body(ref) -> dict:
    """REFERENCE docs come back wrapped ({'body': <json>, 'metadata', ...}),
    matching L7 resolve_anchor's convention. Unwrap + parse to the raw dict."""
    if not isinstance(ref, dict):
        return {}
    body = ref.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except (ValueError, TypeError):
            body = None
    return body if isinstance(body, dict) else {}


def confidence(memory, category: str, name: str) -> dict:
    """Reliability 0..1 for one entity, with a human reason. Deterministic.

    If provenance was recorded it dominates. Otherwise a conservative
    body-shape heuristic (a lesson with an outcome and concrete detail is more
    decision-grade than a bare note). Never raises on a missing entity — a
    missing entity has confidence 0 with reason 'absent'.
    """
    reasons: list[str] = []
    prov = _get_prov(memory, category, name)

    try:
        ent = memory.get_entity(category, name)
    except Exception:
        return {"category": category, "name": name, "confidence": 0.0,
                "reason": "absent", "provenance": prov}

    body = ent.get("body")
    c = 0.0
    if prov.get("recorded"):
        c += W_SOURCE if prov.get("source") else 0.0
        reasons.append("source" if prov.get("source") else "no-source")
        corr = min(1.0, int(prov.get("evidence", 0)) / 3.0)
        c += W_CORROB * corr
        reasons.append(f"evidence={int(prov.get('evidence', 0))}")
        c += W_FALSIF if prov.get("falsifiable") else 0.0
        reasons.append("falsifiable" if prov.get("falsifiable") else "unfalsifiable")
        # shape credit
        if isinstance(body, dict):
            if body.get("lesson") and body.get("outcome"):
                c += W_SHAPE
                reasons.append("lesson+outcome")
            elif body.get("lesson"):
                c += 0.5 * W_SHAPE
                reasons.append("lesson")
    else:
        # Conservative heuristic — no recorded provenance.
        shape = 0.0
        if isinstance(body, dict):
            has_lesson = isinstance(body.get("lesson"), str)
            has_outcome = isinstance(body.get("outcome"), dict)
            if has_lesson and has_outcome:
                shape = W_SHAPE
                reasons.append("lesson+outcome")
            elif has_lesson:
                shape = 0.5 * W_SHAPE
                reasons.append("lesson")
        novel = _text_novelty(body) if isinstance(body, dict) else 0.0
        c = 0.35 + 0.5 * shape + 0.15 * novel
        reasons.append("no-recorded-provenance (heuristic)")

    return {"category": category, "name": name,
            "confidence": round(min(1.0, max(0.0, c)), 3),
            "reason": "; ".join(reasons), "provenance": prov}


# ---------------------------------------------------------------------------
# Store census & coverage
# ---------------------------------------------------------------------------
def snapshot(memory) -> dict:
    """A census of the store across every tier. Always returns a full shape
    (zeros, never silent) so the agent knows its own size."""
    live = memory.list_entities(limit=10000)
    archived = memory.list_archived()
    refs = memory.list_references()
    prov_docs = [r for r in refs if str(r.get("doc_key", "")).startswith(_PROV_PREFIX)]
    by_cat: dict[str, int] = {}
    for e in live:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    try:
        ev = memory.read_events(limit=100000)
        n_events = len(ev) if isinstance(ev, list) else 0
    except Exception:
        n_events = 0
    return {
        "live_entities": len(live), "live_by_category": by_cat,
        "archived": len(archived), "references": len(refs) - len(prov_docs),
        "provenance_records": len(prov_docs), "journal_events": n_events,
    }


def coverage(memory) -> dict:
    """Per-category maturity and blind spots. Categories that only hold notes
    (no decision-bearing lessons) are marked immature — the agent knows where
    its scar tissue is thin."""
    live = memory.list_entities(limit=10000)
    agg: dict[str, dict] = {}
    for e in live:
        cat = e["category"]
        a = agg.setdefault(cat, {"live": 0, "lessons": 0, "hard": 0})
        a["live"] += 1
        body = e.get("body")
        if isinstance(body, dict) and isinstance(body.get("lesson"), str):
            a["lessons"] += 1
            prov = _get_prov(memory, cat, e["name"])
            if prov.get("hard"):
                a["hard"] += 1
    out: dict[str, dict] = {}
    for cat, a in agg.items():
        maturity = min(1.0, 0.4 * (a["lessons"] / 1.0)
                       + 0.4 * min(1.0, a["lessons"] / 3.0)
                       + 0.2 * min(1.0, a["hard"] / 1.0))
        out[cat] = {**a, "maturity": round(maturity, 3),
                    "blind": a["lessons"] == 0}
    return out


# ---------------------------------------------------------------------------
# The anti-hallucination read
# ---------------------------------------------------------------------------
def known_unknowns(memory, query: str, *, limit: int = 10) -> dict:
    """Explicit epistemic verdict for a query. Returns COVERED / THIN /
    UNKNOWN — never an empty silence. The decision-maker uses this to decide
    whether it is safe to act on what it recalls, or must learn first.

    COVERED  -> >=1 high-confidence (decision-grade) hit.
    THIN     -> matches exist but none is high-confidence (not trustworthy
                enough to build a decision on alone).
    UNKNOWN  -> no decision-bearing memory on this topic. A signal to go learn,
                not an empty list.
    """
    try:
        hits = list(memory.search(query, limit=limit))
    except Exception:
        hits = []
    high_conf = []
    for h in hits:
        body = h.get("body")
        if isinstance(body, dict):
            grade = (isinstance(body.get("lesson"), str)
                     and isinstance(body.get("outcome"), dict))
        else:
            grade = False
        prov = _get_prov(memory, h.get("category", ""), h.get("name", ""))
        if grade or prov.get("recorded") or prov.get("hard"):
            high_conf.append(h)
    if high_conf:
        status = "COVERED"
        action = "safe to act on recall"
    elif hits:
        status = "THIN"
        action = "recall is weak; corroborate or de-risk before acting"
    else:
        status = "UNKNOWN"
        action = "no decision-bearing memory; go learn this before acting"
    return {
        "query": query, "status": status, "action": action,
        "hits": len(hits), "high_confidence_hits": len(high_conf),
        "samples": [h.get("name") for h in high_conf[:3]],
    }


# ---------------------------------------------------------------------------
# Verifiable artifact digest (shared with L12 EXCHANGE)
# ---------------------------------------------------------------------------
def content_hash(payload: dict) -> str:
    """Deterministic SHA-256 over the canonical JSON of a payload. Two stores
    that serialize the same lesson identically produce the same digest."""
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       default=str)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
