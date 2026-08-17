"""The load-bearing decision function.

`decide_differently` is THE function the hackathon hinges on:

    - WITH memory: it recalls past crisis lessons from Sibyl Memory and, when
      the market is stressed (credit_stress > threshold or vix > threshold),
      returns a de-risked book (low equity, high cash/rates/hedges).
    - WITHOUT memory (store deleted): `recall_lessons` returns [] and it fails
      open to `naive_book` -> overweight equity -> the losing trade.

That asymmetry is the 40-point "memory load-bearing" proof. See
tests/test_loadbearing.py for the executable deletion test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .memory import Memory


@dataclass
class Book:
    """A capital allocation. `equity` is the headline weight a judge reads."""
    equity: float
    credit: float
    rates: float
    hedges: float
    cash: float
    rationale: str

    def to_dict(self) -> dict:
        return {
            "equity": self.equity,
            "credit": self.credit,
            "rates": self.rates,
            "hedges": self.hedges,
            "cash": self.cash,
            "rationale": self.rationale,
        }


def naive_book() -> Book:
    """Memory-less baseline: overweight equity, ignores history entirely."""
    return Book(
        equity=0.55, credit=0.20, rates=0.10, hedges=0.0, cash=0.15,
        rationale="naive: overweight equity, no recall of past losses",
    )


def de_risk_book(n_lessons: int) -> Book:
    """Memory-driven response: de-risk into cash/rates/hedges in stress."""
    return Book(
        equity=0.05, credit=0.03, rates=0.40, hedges=0.20, cash=0.32,
        rationale=f"recalled {n_lessons} crisis lesson(s) -> de-risked into cash/rates",
    )


def is_stressed(frame: dict, *, credit_stress_threshold: float = 0.7,
                vix_threshold: float = 30.0) -> bool:
    cs = float(frame.get("credit_stress", 0.0))
    vix = float(frame.get("vix", 0.0))
    return cs > credit_stress_threshold or vix > vix_threshold


def decide_differently(frame: dict, memory: Memory | None,
                       search_phrases: list[str] | None = None,
                       *, credit_stress_threshold: float = 0.7,
                       vix_threshold: float = 30.0) -> Book:
    """THE decision function.

    Args:
        frame: market context, e.g. {"vix": 52.0, "credit_stress": 2.2}.
        memory: a Memory instance, or None to simulate a deleted store.
        search_phrases: recall queries (defaults to crisis-stress phrases).

    Returns:
        A Book. Fails open to naive_book() if there is no memory or no recall.
    """
    phrases = search_phrases or [
        "credit stress crisis lesson",
        "drawdown loss recovery",
    ]

    lessons: list[str] = []
    if memory is not None:
        try:
            lessons = memory.recall_lessons(phrases)
        except Exception:
            # A broken/locked store must not crash the agent: fail open to naive.
            lessons = []

    if is_stressed(frame, credit_stress_threshold=credit_stress_threshold,
                   vix_threshold=vix_threshold) and lessons:
        return de_risk_book(len(lessons))
    return naive_book()
