"""Regret Memory — remembering the road not taken (counterfactual memory).

Standard memory stores what *happened*. Regret memory stores what *did not*
happen but should have — the losing path the agent avoided by acting on a
lesson. This is the "soul" layer of the spine:

  * `write_regret`   — persist the counterfactual: the decision taken, the path
                       NOT taken, and what that road would have cost.
  * `recall_regrets` — surface the would-have-lost lessons so a fresh agent
                       "remembers the mistakes it never made" — a stronger,
                       more emotionally-grounded de-risk signal than a bare
                       factual lesson.
  * `regret_urgency` — weight how sharply the counterfactual argues for caution.

It composes with the existing policy: `decide_differently` still runs on factual
lessons, but regret memory adds a second, independent recall channel that pulls
the same direction — and is itself load-bearing (delete it -> no counterfactual
-> the "would have lost 18%" memory vanishes).

Pure addition; existing behavior untouched.
"""

from __future__ import annotations

import json
from typing import Any

from .memory import Memory

REGRET_CATEGORY = "regret"


def write_regret(memory: Memory, name: str, *, taken: str,
                 road_not_taken: str, would_have_lost: float | None = None,
                 frame: dict | None = None) -> dict:
    """Persist a counterfactual memory.

    Args:
        memory: Sibyl store.
        name: unique regret id (e.g. "crisis-2026-1").
        taken: what the agent actually did ("de-risked to cash").
        road_not_taken: the path it avoided ("stayed overweight equity").
        would_have_lost: the % it would have lost had it taken that road.
        frame: optional market context at the time.
    """
    body: dict[str, Any] = {
        "taken": taken,
        "road_not_taken": road_not_taken,
        "regret": (f"remembered the road not taken: had I {road_not_taken} "
                   f"instead of {taken}, I would have lost {would_have_lost}%."),
    }
    if would_have_lost is not None:
        body["would_have_lost"] = would_have_lost
    if frame is not None:
        body["frame"] = frame
    return memory.set_entity(REGRET_CATEGORY, name, body, status="active")


def recall_regrets(memory: Memory, queries: list[str], *, limit: int = 20) -> list[str]:
    """Recall the counterfactual lessons ("I avoided losing X%")."""
    seen: set[str] = set()
    regrets: list[str] = []
    for q in queries:
        for hit in memory.search(q, limit=limit, category=REGRET_CATEGORY):
            body = hit.get("body")
            text = None
            if isinstance(body, dict):
                text = body.get("regret") or body.get("road_not_taken")
            elif isinstance(body, str):
                text = body
            if text and text not in seen:
                seen.add(text)
                regrets.append(text)
    return regrets


def regret_urgency(memory: Memory, queries: list[str], *, limit: int = 20) -> float:
    """How sharply the counterfactuals argue for caution, 0..1.

    Weighted by magnitude of would-have-lost (cap at 30% for a 1.0 urgency).
    Returns 0 when there is no regret memory (so a wiped store -> no urgency).
    """
    seen: set[str] = set()
    worst = 0.0
    for q in queries:
        for hit in memory.search(q, limit=limit, category=REGRET_CATEGORY):
            body = hit.get("body")
            key = json.dumps(body, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            if isinstance(body, dict):
                worst = max(worst, float(body.get("would_have_lost", 0.0) or 0.0))
    return min(1.0, worst / 30.0)


def regret_de_risk_book(memory: Memory, *, n_regrets: int,
                        urgency: float = 1.0) -> dict:
    """The counterfactual-driven defensive book (mirrors policy.de_risk_book).

    Returns a dict shaped like a Book but labelled as regret-driven, so the
    demo can show the two channels (factual + regret) both converging on cash.
    Pure helper; the authoritative Book comes from policy.de_risk_book.
    """
    # equity floor scales down with urgency, capped at the spec's 0.05.
    equity = round(max(0.0, 0.05 * (1.0 - urgency)), 3)
    return {
        "equity": equity,
        "regret_urgency": round(urgency, 3),
        "n_regrets": n_regrets,
        "rationale": (f"remembered {n_regrets} road(s) not taken "
                      f"(urgency={urgency:.2f}) -> de-risk to {equity} equity"),
    }
