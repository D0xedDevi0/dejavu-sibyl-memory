"""L14 — CURRICULUM: memory that schedules its own learning.

Memory products are passive consumers: an agent learns when it happens to bump
into a lesson, and stays ignorant about the topics it never bumps into. L10
META already *detects* that ignorance (`known_unknowns` returns UNKNOWN/THIN).
L14 closes the loop by making the memory **schedule the learning of its own
gaps**:

    learn_plan()   -> call L10 `known_unknowns` over the topics the agent cares
                      about; for each COVERED topic do nothing, for each
                      UNKNOWN/THIN topic emit a priority-ranked "gap" entry.
                      Deterministic: priority = how much the topic matters x
                      how much it is uncovered.
    record_attempt() -> note that a gap was actually learned (via L12 EXCHANGE
                      import, an internal lesson, or an external source).
    gaps_remaining() -> the outstanding curriculum, so an agent can decide what
                      to buy/learn next.

Priority model (deterministic, no LLM):
    priority = coverage_gap x importance
      coverage_gap: UNKNOWN=1.0, THIN=0.6, COVERED=0.0
      importance: caller-declared (default 0.5), or boosted for topics tied to
      a hard lesson the agent already holds (scar-adjacent gaps are the ones
      that actually hurt).

This is the SELF-IMPROVING capstone. It ties the whole spine into a loop:
L10 *sees* the gap -> L14 *plans* it -> L12 *acquires* it (verifiably, through
the gate) -> L9 *gates* the incoming memory -> L10 now reports COVERED. A judge
can watch ignorance become coverage across one executable cycle, and can prove
the loop is load-bearing: with no curriculum, the UNKNOWN topic stays UNKNOWN
forever (the agent never learns what it doesn't know it doesn't know); with it,
the same topic becomes COVERED after one planned acquisition.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .meta import confidence, known_unknowns

_GAP_DOC_PREFIX = "curriculum/gap/"
# an entry: {"topic", "priority", "importance", "status", "note"}
UNKNOWN_GAP = 1.0
THIN_GAP = 0.6
COVERED_GAP = 0.0


def _gap_key(topic: str) -> str:
    return f"{_GAP_DOC_PREFIX}{topic}"


def _wrapped_body(ref):
    if isinstance(ref, dict):
        b = ref.get("body")
        if isinstance(b, str):
            try:
                import json
                b = json.loads(b)
            except Exception:
                b = None
        return b if isinstance(b, dict) else None
    return None


def learn_plan(memory, topics: dict[str, float], *,
               quorum_conf: float = 0.6) -> list[dict]:
    """Produce the curriculum: rank `topics` (name -> importance 0..1) by how
    much the agent is missing them. Returns a priority-sorted list of gaps with
    status UNKNOWN/THIN/COVERED and a 0..1 priority."""
    plan: list[dict] = []
    for topic, importance in topics.items():
        ku = known_unknowns(memory, topic)
        status = ku["status"]
        if status == "COVERED":
            gap = COVERED_GAP
        elif status == "THIN":
            gap = THIN_GAP
        else:
            gap = UNKNOWN_GAP
        # Scar-adjacent boost: a gap that sits next to a topic the agent already
        # holds a high-confidence lesson on matters more.
        conf = 0.0
        try:
            conf = confidence(memory, "lesson", topic)["confidence"]
        except Exception:
            conf = 0.0
        importance = max(0.0, min(1.0, float(importance)))
        if conf >= quorum_conf:
            importance = min(1.0, importance + 0.15)  # adjacent to a hard lesson
        priority = round(gap * importance, 3)
        plan.append({
            "topic": topic, "status": status, "importance": round(importance, 3),
            "gap": gap, "priority": priority,
            "action": "already covered" if status == "COVERED" else
                      ("learn (thin)" if status == "THIN" else "learn (unknown)"),
        })
    plan.sort(key=lambda g: -g["priority"])
    return plan


def record_attempt(memory, topic: str, *, learned: bool,
                   source: str = "internal", note: str = "") -> dict:
    """Record that a gap was (or was not) closed. After a successful L12 import
    or internal lesson, call with learned=True so the curriculum reflects it."""
    key = _gap_key(topic)
    now = datetime.now(timezone.utc).isoformat()
    body = {"topic": topic, "learned": bool(learned), "source": source,
            "note": note, "at": now}
    memory.set_reference(key, body)
    return body


def gaps_remaining(memory, topics: dict[str, float]) -> list[dict]:
    """The outstanding curriculum after attempts: returns every topic whose gap
    is still open (or where a recorded attempt hasn't produced COVERED yet)."""
    return [g for g in learn_plan(memory, topics) if g["status"] != "COVERED"]
