"""Action authority + compact decision receipt (proposal -> guard -> approved -> onchain).

``decide_differently`` fails OPEN to a naive book when memory is absent — that
is the research demo's load-bearing deletion proof, and it is left untouched.
This module adds the guard layer: before a book becomes an onchain action, the
L11 guard checks stored hard lessons against the proposed allocation.  The
compact ``DecisionReceipt`` records the whole authority chain — proposal,
actual guard verdict, approved allocation, store identifiers/root (captured
BEFORE the onchain step), and the onchain outcome with an explicit ``live_tx``
flag (absent, never invented).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from .base_action import execute
from .guard import guard_book
from .policy import Book, de_risk_book
from .sovereign import memory_root


def _hex_digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


@dataclass
class DecisionReceipt:
    """Honest record of one decide→guard→execute cycle.  Distinguishes what the
    policy PROPOSED from what the guard APPROVED before any onchain step —
    so a blocked allocation is never executed."""
    decision_id: str
    timestamp_utc: str
    proposed: dict
    guard: dict
    approved: dict
    recalled_ids: list[str]     # entity names the policy's search found
    memory: dict                # {tenant_id, root, db_path} — root captured BEFORE onchain
    onchain: dict

    def as_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "timestamp_utc": self.timestamp_utc,
            "proposed": self.proposed,
            "guard": self.guard,
            "approved": self.approved,
            "recalled_ids": self.recalled_ids,
            "memory": self.memory,
            "onchain": self.onchain,
        }


def apply_guard(proposed: Book, verdict) -> Book:
    """Bounded guard: a BLOCK verdict replaces the proposed book with the
    de-risked defensive allocation.  ALLOW / WARN pass the proposal through
    unchanged so the verdict is recorded, not dropped."""
    if verdict.verdict == "block":
        return de_risk_book(
            len(verdict.matched), risk=1.0,
            rationale=(
                f"guard BLOCKED proposed equity {proposed.equity:.2f}: "
                "vetoed as a recorded-loss replay"
            ),
        )
    return proposed


def decide_and_execute(memory, frame: dict, proposed: Book, config, *,
                       recalled_ids: list[str] | None = None) -> DecisionReceipt:
    """Wrap an already-computed proposal through the full action-authority
    chain and return a compact, honest DecisionReceipt.

    ``memory`` must be open (guard book, root fingerprint).  The store root
    is captured BEFORE the onchain step so it reflects the decision-time
    state.  ``recalled_ids`` carries the entity names the policy found via
    recall_lessons (distinct from the guard's hard-lesson ``matched`` list).
    """
    verdict = guard_book(memory, frame, proposed.equity)
    approved = apply_guard(proposed, verdict)

    # Capture root BEFORE onchain action (the store is read-only here).
    root = memory_root(memory)

    onchain = execute(approved, config)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    decision_id = _hex_digest(
        root["tenant"], root["root"], ts,
        json.dumps(proposed.to_dict(), sort_keys=True, default=str),
    )[:16]

    return DecisionReceipt(
        decision_id=decision_id,
        timestamp_utc=ts,
        proposed=proposed.to_dict(),
        guard=verdict.to_dict(),
        approved=approved.to_dict(),
        recalled_ids=list(recalled_ids or []),
        memory={
            "tenant_id": root["tenant"],
            "root": root["root"],
            "db_path": str(memory.db_path),
        },
        onchain=onchain.as_dict(),
    )