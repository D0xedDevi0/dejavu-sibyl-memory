"""L11 — GUARD: memory that ACTS.

Retrieval-driven memory is passive: it *informs* a decision but never stops
one. An agent with a text-search miss on recall will happily repeat the exact
harm it once recorded — the memory "I remember what happened last time" is
recalled too late or not at all. THE SPINE's L11 closes that by giving memory
**veto power**: a stored hard lesson becomes a constraint the planner cannot
walk past, independent of whether a fuzzy recall phrase matched.

The macro embodiment is exact: Session A records a crisis hard lesson (outcome
drawdown -0.24). Later, even if the recall phrase in `decide_differently`
text-misses, GUARD still sees the hard lesson + a stressed frame + a proposed
overweight-equity book and BLOCKS it — the same -18% repeat is stopped at the
action layer, not just the recall layer. That is a second, load-bearing line of
defense: memory that says "no," not just "remember."

    hard_lessons()  -> the non-negotiable set (prov.hard OR outcome drawdown).
    assess()        -> {allow | warn | block} + rationale for a proposed action.
    guard_book()    -> the decision-friendly wrapper over the macro book.

Deterministic, no LLM. A store with no hard lessons is permissive (nothing to
guard against) and says so — no silent "allowed."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .meta import _get_prov

# A proposed equity weight above this under stress, when a hard crisis lesson
# exists, is a BLOCK (it reproduces the -18% class of loss).
BLOCK_EQUITY = 0.20
# Above this but under the block line, with a hard lesson + stress -> warn.
WARN_EQUITY = 0.051

HARD_DRAWDOWN = -0.10   # lessons with outcome drawdown at/below this are hard


@dataclass
class GuardVerdict:
    verdict: str                 # allow | warn | block
    action: str
    rationale: str
    matched: list = field(default_factory=list)
    frame_stressed: bool = False

    @property
    def blocked(self) -> bool:
        return self.verdict == "block"

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "action": self.action,
                "rationale": self.rationale, "matched": self.matched,
                "frame_stressed": self.frame_stressed}


def hard_lessons(memory) -> list[dict]:
    """Every live non-negotiable lesson (category 'lesson'), with its text."""
    out: list[dict] = []
    for e in memory.list_entities(category="lesson", status="active",
                                  limit=10000):
        prov = _get_prov(memory, "lesson", e["name"])
        body = e.get("body")
        hard = bool(prov.get("hard"))
        if isinstance(body, dict):
            outcome = body.get("outcome")
            if isinstance(outcome, dict):
                dd = outcome.get("max_drawdown") or outcome.get("drawdown")
                if isinstance(dd, (int, float)) and dd <= HARD_DRAWDOWN:
                    hard = True
        if hard:
            text = body.get("lesson") if isinstance(body, dict) else body
            out.append({"name": e["name"], "lesson": text, "provenance": prov})
    return out


def assess(memory, action: str, *, context: dict | None = None,
           proposed_equity: float | None = None) -> GuardVerdict:
    """General guard: decide whether `action` is safe given stored hard lessons
    and the current context. The macro decision passes `proposed_equity`; other
    domains can call `guard_book` or extend this with their own risk field."""
    hard = hard_lessons(memory)
    if not hard:
        return GuardVerdict(
            "allow", action,
            "no hard lessons recorded — nothing to guard against", [])
    # Only guard when the context looks risky; otherwise allow but note.
    cs = float((context or {}).get("credit_stress", 0.0))
    vix = float((context or {}).get("vix", 0.0))
    stressed = cs > 0.7 or vix > 30.0
    matched = [h["name"] for h in hard]
    names = ", ".join(matched)

    if proposed_equity is None:
        return GuardVerdict("allow", action,
                            "no risk field to evaluate; hard lessons present but "
                            f"not triggered ({names})", matched, stressed)

    if stressed and proposed_equity > BLOCK_EQUITY:
        return GuardVerdict(
            "block", action,
            f"stressed frame + hard lesson {names}: proposed equity "
            f"{proposed_equity:.2f} reproduces the recorded loss class — vetoed",
            matched, stressed)
    if stressed and proposed_equity > WARN_EQUITY:
        return GuardVerdict(
            "warn", action,
            f"stressed frame + hard lesson {names}: proposed equity "
            f"{proposed_equity:.2f} still above the defensive floor — de-risk more",
            matched, stressed)
    return GuardVerdict(
        "allow", action,
        f"hard lesson present ({names}) but action is already defensive", matched,
        stressed)


def guard_book(memory, frame: dict, proposed_equity: float) -> GuardVerdict:
    """Guard over the macro allocation. `proposed_equity` is the equity weight a
    decision function wants to deploy (e.g. naive 0.55)."""
    return assess(memory, "deploy_book", context=frame,
                  proposed_equity=proposed_equity)
