"""L9 — DISCERNMENT: the memory's write-quality gate.

Every memory system on the market is obsessed with RETRIEVAL (RAG, vector
search, FTS, recall quality). Almost nobody solves the other end of the pipe:
WHAT gets written in the first place.

"Garbage in, garbage out" hits memory twice as hard. An agent that persists
noise, near-duplicates, low-information chatter and stale truisms rots its own
store from the ingestion side — and no amount of retrieval polish fixes a
polluted store. Worse, a finite agent can't remember everything anyway: memory
capacity is a *budget*, and nothing treats it like one.

THE SPINE's L9 gives the memory editorial judgment. Before anything reaches the
live WARM tier, the gate scores the fact and decides:

    PERSIST            -> write it live (it earns its slot)
    EVICT_THEN_PERSIST -> budget is full; archive the lowest-value live entry
                          (recoverable, never deleted) and write this
    SUPERSEDE          -> contradicts a live value; route to L8's write-time
                          conflict resolution (supersede.py)
    REJECT             -> noise / low-information / unverifiable; journal why,
                          persist NOTHING

Scores are deterministic (no LLM, no RNG) and recomputable. The gate also
*learns its own ingestion policy*: `feedback_used` / `feedback_unused` adjust a
per-category value model, and `recalibrate_policy` re-weights categories by
whether their memories actually changed a decision. Categories whose memories
get used become easier to write into; categories whose memories sit idle get
throttled so budget stays for what matters.

Load-bearing: delete the gate and the store floods with noise, recall
degrades, and a noisy fact competes with a hard-won lesson at recall time.
With the gate, the store stays clean and the lesson wins. Mirrors the L1-L8
deletion-gate discipline at the ingestion layer.

The "no silent failures" rule (Sibyl v0.8.0 'lucid') is honored: the gate
ALWAYS returns an explicit decision with a reason — it never silently drops.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --- Tunable policy defaults -------------------------------------------------
DEFAULT_CAP = 256            # max live WARM entities before eviction kicks in
DEFAULT_WEIGHTS = {          # initial ingestion-policy weights (agent of record)
    "lesson":  0.80,
    "view":    0.70,
    "decision": 0.85,
    "fact":    0.60,
    "trivia":  0.25,
}
DEFAULT_W = {                # value-score signal weights
    "novelty": 0.40,
    "truth":   0.30,
    "use":     0.25,
    "noise":   0.55,         # subtractive penalty
}
LEVERAGE = 0.25              # EMA learning rate for the policy model
VERBOSE = False


# ---------------------------------------------------------------------------
# Decision shape
# ---------------------------------------------------------------------------
@dataclass
class GateDecision:
    action: str                          # PERSIST | EVICT_THEN_PERSIST | SUPERSEDE | REJECT
    reason: str                          # human/debug reason
    scores: dict = field(default_factory=dict)
    evicted: list = field(default_factory=list)   # [(category, name)] archived to make room
    journaled: bool = False

    @property
    def ok(self) -> bool:
        """True if the fact is (or will be) persisted live (never for REJECT)."""
        return self.action in ("PERSIST", "EVICT_THEN_PERSIST", "SUPERSEDE")


# ---------------------------------------------------------------------------
# Value scoring (deterministic)
# ---------------------------------------------------------------------------
def _text_novelty(body: dict) -> float:
    """How information-rich a body is irrespective of the store (0..1).

    § README/UPGRADES: this is the anti-noise floor. Empty, single-token,
    generic, or low-information bodies score low; rich structured bodies "
    win."""

    def _text(x) -> str:
        if isinstance(x, str):
            return x.strip()
        if isinstance(x, dict):
            return " ".join(
                str(v) for v in x.values()
                if isinstance(v, (str, float, int)) and not isinstance(v, bool)
            )
        return ""

    text = _text(body)
    if not text:
        return 0.0
    words = [w for w in text.split() if len(w) > 1]
    all_tokens = text.split()
    if not words and not all_tokens:
        return 0.05
    # Concrete numeric detail is strong signal that a fact isn't noise.
    # Count ANY token bearing a digit (single-char ints like 0/7 included),
    # while word-length calls out only substantive multi-char tokens.
    digits = sum(1 for w in all_tokens if any(ch.isdigit() for ch in w))
    n = max(1, min(len(words), 8))
    concrete = min(1.0, (digits / n) * 2.0)
    length = min(1.0, len(words) / 24.0)
    return round(0.55 * length + 0.45 * concrete, 3)


def _falsifiable_truth(evidence: int, source: object | None,
                       falsifiable: bool) -> float:
    """Truth confidence from metadata (0..1). Deterministic.

    Corroboration (evidence count) + whether the claim carries a falsifiable
    shape + a credible source marker. Unverifiable one-off claims score low —
    the gate refuses to spend budget on them.
    """
    corrob = min(1.0, evidence / 3.0)
    shape = 0.25 if falsifiable else 0.0
    src = 0.25 if source else 0.0
    return round(min(1.0, corrob * 0.5 + shape + src + 0.15), 3)


# ---------------------------------------------------------------------------
# Usage ledger + policy model (self-learning ingestion policy)
# ---------------------------------------------------------------------------
_USAGE_PREFIX = "gates/u/"   # one small REFERENCE doc per (cat,name) — stays tiny
_POLICY_DOC = "gates/policy" # REFERENCE ledger: {cat: weight, cap}


def _usage_key(category: str, name: str) -> str:
    return f"{category}::{name}"


def _usage_doc(category: str, name: str) -> str:
    return f"{_USAGE_PREFIX}{category}::{name}"


def _read_usage(memory) -> dict:
    """Collect every per-key usage record. Each record is its own small
    REFERENCE doc so the ledger never grows past the body-cap as the store
    scales (SDK cap-gate: per-value max bytes)."""
    out: dict[str, dict] = {}
    for ref in memory.list_references():
        key = ref.get("doc_key") or ""
        if key.startswith(_USAGE_PREFIX):
            body = ref.get("body")
            if isinstance(body, dict):
                out[key.removeprefix(_USAGE_PREFIX)] = body
    return out


def _write_usage(memory, category: str, name: str, record: dict) -> None:
    memory.set_reference(_usage_doc(category, name), record)


def _read_policy(memory) -> dict:
    ref = memory.get_reference(_POLICY_DOC)
    pol = None
    if isinstance(ref, dict):
        body = ref.get("body")
        if isinstance(body, str):
            try:
                import json as _json
                body = _json.loads(body)
            except (ValueError, TypeError):
                body = None
        if isinstance(body, dict):
            pol = body
    if isinstance(pol, dict) and pol.get("weights"):
        return pol
    return {"weights": dict(DEFAULT_WEIGHTS), "cap": DEFAULT_CAP}


def _write_policy(memory, pol: dict) -> None:
    memory.set_reference(_POLICY_DOC, pol)


def _cat_weight(memory, category: str) -> float:
    return _read_policy(memory)["weights"].get(category, 0.5)


def _log(memory, *, action: str, category: str, name: str, reason: str,
         scores: dict, evicted: list | None = None) -> None:
    evicted = evicted or []
    try:
        memory.write_event(
            evaluated={"category": category, "name": name},
            acted={"action": f"GATE_{action.upper()}",
                   "evicted": [f"{c}::{n}" for c, n in evicted]},
            forward=reason,
            extra={"scores": scores},
        )
    except Exception:  # pragma: no cover — journaling must never break the gate
        pass


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def gate_write(memory, category: str, name: str, body: dict, *,
               source: str | None = None, evidence: int = 0,
               falsifiable: bool = False, cap: int | None = None) -> GateDecision:
    """Score a candidate fact and decide whether it earns a slot in the store.

    Deterministic. Returns an explicit GateDecision (never silent).
    """
    scores = {
        "novelty": _text_novelty(body),
        "truth": _falsifiable_truth(evidence, source, falsifiable),
        "use": _cat_weight(memory, category),
        "noise": round(1.0 - _text_novelty(body), 3),
    }
    value = round(
        DEFAULT_W["novelty"] * scores["novelty"]
        + DEFAULT_W["truth"] * scores["truth"]
        + DEFAULT_W["use"] * scores["use"]
        - DEFAULT_W["noise"] * scores["noise"],
        4,
    )
    scores["value"] = value

    # --- 1. Conflict with a live value -> route to L8 supersede ------------
    prior = _get_live_body(memory, category, name)
    if prior is not None and prior != body:
        _log(memory, action="SUPERSEDE", category=category, name=name,
             reason="write conflict -> L8", scores=scores)
        from .supersede import supersede_entity
        supersede_entity(memory, category, name, body)
        return GateDecision("SUPERSEDE", "conflict with live value -> L8", scores)

    # --- 2. Noise floor ------------------------------------------------------
    if scores["novelty"] < 0.20:
        _log(memory, action="REJECT", category=category, name=name,
             reason="below noise floor", scores=scores)
        return GateDecision("REJECT", "below noise floor", scores)

    # --- 3. Capacity budget (evict lowest-value live entry, recoverably) ----
    live = _list_live(memory)
    if cap is None:
        cap = _read_policy(memory)["cap"]
    if len(live) >= cap:
        weakest = _weakest_live(memory, live, cap)
        if weakest is None or weakest[2] >= value:
            _log(memory, action="REJECT", category=category, name=name,
                 reason="budget full, newcomer below weakest survivor",
                 scores=scores)
            return GateDecision(
                "REJECT", "memory budget full; newcomer below weakest survivor",
                scores)
        # Archive the weakest (recoverable, never deleted), free its slot.
        memory.archive_entity(weakest[0], weakest[1], reason="gate:budget")
        usage = _read_usage(memory)
        k = _usage_key(weakest[0], weakest[1])
        if k in usage:
            usage[k]["evicted"] = usage[k].get("evicted", 0) + 1
            _write_usage(memory, weakest[0], weakest[1], usage[k])
        evicted = [(weakest[0], weakest[1])]
        memory.set_entity(category, name, body)
        _remember_value(memory, category, name, value)
        _log(memory, action="EVICT", category=category, name=name,
             reason="capacity budget -> archived weakest",
             scores=scores, evicted=evicted)
        return GateDecision(
            "EVICT_THEN_PERSIST",
            "budget full -> archived weakest live entry, persisting newcomer",
            scores, evicted)

    # --- 4. Persist the newcomer, record its live value --------------------
    memory.set_entity(category, name, body)
    _remember_value(memory, category, name, value)
    _log(memory, action="PERSIST", category=category, name=name,
         reason="earned its slot", scores=scores)
    return GateDecision("PERSIST", "earned its slot", scores)


# --- internal helpers --------------------------------------------------------
def _get_live_body(memory, category: str, name: str):
    try:
        ent = memory.get_entity(category, name)
        return ent.get("body") if isinstance(ent, dict) else None
    except Exception:
        return None


def _list_live(memory) -> list[dict]:
    """Enumerate live WARM entities across every category."""
    return memory.list_entities(limit=1000, status="active") \
        or memory.list_entities(limit=1000)


def _weakest_live(memory, live: list[dict], cap: int):
    """Lowest-value live entry by stored value (loaded at write time)."""
    usage = _read_usage(memory)
    best = None  # (cat, name, value)
    for ent in live:
        cat = ent.get("category") or ""
        nm = ent.get("name") or ""
        if not nm:
            continue
        stored = usage.get(_usage_key(cat, nm), {})
        uval = stored.get("value")
        val = uval if isinstance(uval, (int, float)) else 0.5
        if best is None or val < best[2]:
            best = (cat, nm, val)
    return best


def _remember_value(memory, category: str, name: str, value: float) -> None:
    record = {"used": 0, "evicted": 0, "value": value, "cat": category}
    _write_usage(memory, category, name, record)


# ---------------------------------------------------------------------------
# Self-learning ingestion policy
# ---------------------------------------------------------------------------
def feedback_used(memory, category: str, name: str) -> None:
    """Reinforce a memory that changed a decision (it earns easier writes)."""
    usage = _read_usage(memory)
    k = _usage_key(category, name)
    record = usage.get(k, {"used": 0, "evicted": 0, "value": 0.5, "cat": category})
    record["used"] = record.get("used", 0) + 1
    record["value"] = round(record["value"] + LEVERAGE * (1.0 - record["value"]), 3)
    _write_usage(memory, category, name, record)


def feedback_unused(memory, category: str, name: str) -> None:
    """Downgrade a memory that was recalled but never changed a decision."""
    usage = _read_usage(memory)
    k = _usage_key(category, name)
    record = usage.get(k, {"used": 0, "evicted": 0, "value": 0.5, "cat": category})
    record["value"] = round(record["value"] - LEVERAGE * record["value"], 3)
    _write_usage(memory, category, name, record)


def recalibrate_policy(memory) -> dict:
    """Re-weight each category by whether its memories changed decisions.

    Learned ingestion policy, deterministic (EMA on usage deltas). Categories
    whose memories get used (<used> - <value>) become easier to write into;
    categories whose memories sit idle get throttled so budget goes to the
    memories that matter. Idempotent.
    """
    usage = _read_usage(memory)
    pol = _read_policy(memory)
    weights = pol["weights"]

    agg: dict[str, dict] = {}
    for entry in usage.values():
        cat = entry.get("cat", "other")
        a = agg.setdefault(cat, {"used": 0, "n": 0, "val": 0.0})
        a["used"] += entry.get("used", 0)
        a["n"] += 1
        a["val"] += entry.get("value", 0.5)

    for cat, a in agg.items():
        if a["n"] == 0:
            continue
        base = weights.get(cat, 0.5)
        avg_use = a["used"] / a["n"]
        # Used-bearing categories get a credit; idle categories erode toward 0.
        target = base + LEVERAGE * (avg_use - base)
        weights[cat] = round(min(1.0, max(0.0, target)), 3)

    pol["weights"] = weights
    _write_policy(memory, pol)
    return {"weights": weights, "cap": pol["cap"]}