"""L15 — DISTILL: memory that compresses its scar tissue into capability.

Every memory system stores lessons as TAPE: N similar lessons sit as N scattered
notes, each firing only on a narrow recall query that happens to match its exact
wording. Nobody compresses the corpus. The result is that an agent with five
crisis lessons still fails on a NEW crisis it hasn't seen word-for-word —
because it has recall, not judgment.

THE SPINE's L15 turns memory into capability. It mines the store for the
recurring INVARIANT behind many loss-lessons and compresses it into a single
decision RULE:

    distill_rule()  -> read every live lesson that carries a structured frame +
                       a painful outcome (a scar, not a note). Cluster them, and
                       learn ONE threshold: the most conservative risk level at
                       which the protective action fired across all survivors
                       (minus a safety margin). Output a rule dict:
                       {threshold, n_lessons, protective_action}.

    decide_with_skill() -> apply the rule to a NEW frame: if its risk_score
                       clears the learned threshold, take the protective action
                       (de-risk to the equity floor); else hold. The threshold
                       is a monotonic learned boundary — so a frame that NONE of
                       the stored lessons ever mentioned (e.g. a pure-volatility
                       spike, when every stored scar was credit-stress-driven)
                       now triggers, because the distilled rule captured the
                       underlying invariant, not the surface wording.

Load-bearing mirror: five credit-stress crisis lessons do NOT de-risk a novel
pure-volatility crisis frame through raw text recall (the words don't match).
But the distilled rule — which never saw a vol spike either — DOES, because it
learned the risk threshold that all five scars shared. That is memory as
judgment: five experiences, one transferable capability.

Deterministic (no LLM/RNG). Honest when under-sampled: fewer than `min_samples`
scars -> returns no rule (and says why) rather than fabricating one from noise.
The distilled rule is itself written back as a decision-grade lesson (so L10
confidence, L12 export, L11 guard all see it) with provenance recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import de_risk_book, naive_book, risk_score

DISTILL_NAME = "distilled:protect-capital"
MIN_SAMPLES = 2        # scars needed before a rule is trustworthy
MARGIN = 0.05          # safety margin below the most conservative observed risk
SCAR_DRAWDOWN = -0.05  # a lesson is a 'scar' if its outcome shows at least this pain
PROTECT_FLOOR = 0.05   # the equity floor the protective action targets


def _scar_lessons(memory) -> list[dict]:
    """Live lessons that carry a structured frame AND a painful outcome."""
    out: list[dict] = []
    try:
        ents = memory.list_entities(category="lesson", status="active",
                                    limit=10000)
    except Exception:
        ents = []
    for e in ents:
        body = e.get("body")
        if not isinstance(body, dict):
            continue
        if not isinstance(body.get("frame"), dict):
            continue
        outcome = body.get("outcome")
        if isinstance(outcome, dict):
            dd = outcome.get("max_drawdown") or outcome.get("drawdown")
            if isinstance(dd, (int, float)) and dd <= SCAR_DRAWDOWN:
                out.append({"name": e["name"], "body": body})
    return out


def distill_rule(memory, *, min_samples: int = MIN_SAMPLES,
                 margin: float = MARGIN) -> dict | None:
    """Learn the protective-decision threshold from every crisis scar.

    Returns a rule dict, or None when there are too few scars to trust a rule
    (honest under-sampling — see L14: this is a curriculum gap, not a guess).
    """
    scars = _scar_lessons(memory)
    if len(scars) < min_samples:
        return None
    risks = [risk_score(s["body"]["frame"]) for s in scars]
    # Most conservative observed trigger, minus safety margin, floored at 0.
    threshold = max(0.0, min(risks) - margin)
    rule = {
        "name": DISTILL_NAME,
        "n_lessons": len(scars),
        "threshold": round(threshold, 4),
        "protective_action": "de-risk to equity floor",
        "protective_floor_equity": PROTECT_FLOOR,
        "sources": [s["name"] for s in scars],
    }
    # Persist the distilled rule as a decision-grade lesson + provenance so the
    # rest of the spine (L10 confidence, L11 guard, L12 export) can use it.
    memory.set_entity("lesson", DISTILL_NAME, {
        "lesson": ("learned protective threshold from N crisis scars: "
                   f"risk_score > {round(threshold,3)} -> de-risk to "
                   f"equity {PROTECT_FLOOR}"),
        "rule": rule, "distilled": True,
        "frame": {"_distilled_from": len(scars)},
        "outcome": {"distilled": True},
    }, status="active")
    from .meta import record_provenance
    record_provenance(memory, "lesson", DISTILL_NAME, source="fleet-distill",
                      evidence=len(scars), falsifiable=True, hard=True)
    return rule


def decide_with_skill(memory, frame: dict, *, min_samples: int = MIN_SAMPLES,
                      margin: float = MARGIN):
    """Apply the distilled rule to a NEW frame. De-risks when the frame's risk
    clears the learned threshold; otherwise returns the naive (calm) book.
    If the store hasn't enough scars to distill, fails open to naive (honest)."""
    rule = distill_rule(memory, min_samples=min_samples, margin=margin)
    if rule is None:
        return naive_book()
    if risk_score(frame) > rule["threshold"]:
        return de_risk_book(rule["n_lessons"], risk=risk_score(frame))
    return naive_book()
