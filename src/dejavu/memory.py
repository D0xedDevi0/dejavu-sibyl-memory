"""Sibyl Memory wrapper for the dejavu loop.

Thin, typed facade over `sibyl_memory_client.MemoryClient` covering all five
storage tiers (HOT state / WARM entities / COLD journal / REF reference / ARCH
archive) plus the Learner (self-learning / skill proposals).

The load-bearing calls for the hackathon are `write_lesson`, `recall_lessons`,
and `search` — these are what make memory drive the decision. See README for
exact file/line pointers for judges.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sibyl_memory_client import DEFAULT_TENANT, Learner, MemoryClient

log = logging.getLogger(__name__)

LESSON_CATEGORY = "lesson"


def json_loads_any(text: Any) -> Any:
    """Tolerantly parse a JSON string body, else return it as-is."""
    if not isinstance(text, str):
        return text
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return text


class Memory:
    """Local, headless, file-backed Sibyl store (no account, no network)."""

    def __init__(self, db_path: str | Path, *, tenant_id: str | None = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.tenant_id = tenant_id or DEFAULT_TENANT
        # `local()` returns a client whose `.storage` is a property (not a method).
        kw: dict[str, Any] = {}
        if tenant_id:
            kw["tenant_id"] = tenant_id
        self.client = MemoryClient.local(str(self.db_path), **kw)
        self._learner = None  # lazy: Learner(st) requires the Storage property

    # ---- lifecycle --------------------------------------------------------
    def close(self) -> None:
        if self.client is not None:
            self.client.storage.close()

    @property
    def exists(self) -> bool:
        return self.db_path.exists() and self.db_path.stat().st_size > 0

    def delete_store(self) -> None:
        """Wipe the entire store. This is what breaks a memory-less agent."""
        self.close()
        self.db_path.unlink(missing_ok=True)

    # ---- WARM: entities (single source of truth per (category, name)) -----
    def write_lesson(self, name: str, lesson: str, *, frame: dict | None = None,
                     outcome: dict | None = None, status: str = "active") -> dict:
        body: dict[str, Any] = {"lesson": lesson}
        if frame is not None:
            body["frame"] = frame
        if outcome is not None:
            body["outcome"] = outcome
        return self.client.set_entity(LESSON_CATEGORY, name, body, status=status)

    def get_lesson(self, name: str) -> dict:
        return self.client.get_entity(LESSON_CATEGORY, name)

    def delete_lesson(self, name: str) -> bool:
        """Delete ONE lesson. The 'forgetting' analog: removes that lesson's
        influence while leaving the rest of the store intact."""
        return self.client.delete_entity(LESSON_CATEGORY, name)

    def list_lessons(self, *, status: str | None = None, limit: int = 100) -> list[dict]:
        return self.client.list_entities(LESSON_CATEGORY, status=status, limit=limit)

    # ---- generic entities (used by THE FLEET: any category/name) ----------
    def set_entity(self, category: str, name: str, body: dict,
                   *, status: str = "active") -> dict:
        return self.client.set_entity(category, name, body, status=status)

    def gated_write(self, category: str, name: str, body: dict, *,
                    source: str | None = None, evidence: int = 0,
                    falsifiable: bool = False, cap: int | None = None):
        """L9 DISCERNMENT write path: score the fact, and only persist it if it
        earns its slot (or evicts the weakest live entry to ARCH recoverably to
        make room). Deterministic, returns an explicit GateDecision."""
        from .gates import gate_write  # lazy: keeps memory.py light
        return gate_write(self, category, name, body, source=source,
                          evidence=evidence, falsifiable=falsifiable, cap=cap)

    # ---- L10 META: memory that knows itself --------------------------------
    def record_provenance(self, category: str, name: str, *,
                          source: str | None = None, evidence: int = 0,
                          falsifiable: bool = False, hard: bool = False) -> None:
        """Persist why a memory is (or isn't) trusted. Call after a write so
        `confidence` is grounded, not guessed. `hard` marks a non-negotiable
        lesson that feeds L11 GUARD."""
        from .meta import record_provenance as _rp
        _rp(self, category, name, source=source, evidence=evidence,
            falsifiable=falsifiable, hard=hard)

    def snapshot(self) -> dict:
        """Census of the store across every tier (live/archived/ref/journal)."""
        from .meta import snapshot as _snap
        return _snap(self)

    def coverage(self) -> dict:
        """Per-category maturity + blind spots (where scar tissue is thin)."""
        from .meta import coverage as _cov
        return _cov(self)

    def confidence(self, category: str, name: str) -> dict:
        """Reliability 0..1 for one entity, grounded in recorded provenance."""
        from .meta import confidence as _conf
        return _conf(self, category, name)

    def known_unknowns(self, query: str, *, limit: int = 10) -> dict:
        """Anti-hallucination read: COVERED / THIN / UNKNOWN for a query."""
        from .meta import known_unknowns as _ku
        return _ku(self, query, limit=limit)

    # ---- L11 GUARD: memory that acts ---------------------------------------
    def hard_lessons(self) -> list[dict]:
        """The non-negotiable lessons (prov.hard OR serious outcome drawdown)."""
        from .guard import hard_lessons as _hl
        return _hl(self)

    def guard_book(self, frame: dict, proposed_equity: float):
        """Veto power over the macro allocation: allow/warn/block a book weight
        given stored hard lessons + current stress. Returns a GuardVerdict."""
        from .guard import guard_book as _gb
        return _gb(self, frame, proposed_equity)

    # ---- L12 EXCHANGE: memory that travels ---------------------------------
    def export_lesson(self, name: str, *, price_wei: int = 1_000_000_000) -> dict:
        """Package a live lesson (+ provenance) into a verifiable artifact."""
        from .exchange import export_lesson as _ex
        return _ex(self, name, price_wei=price_wei)

    def import_lesson(self, artifact: dict, *, cap: int | None = None,
                      credit_seller=None) -> dict:
        """Verify + L9-gate a foreign lesson into this store, record provenance,
        journal the purchase, optionally credit the seller's earnings ledger."""
        from .exchange import import_lesson as _im
        return _im(self, artifact, cap=cap, credit_seller=credit_seller)

    def verify_artifact(self, artifact: dict) -> dict:
        """Confirm an exported artifact is intact (content-hash check)."""
        from .exchange import verify_artifact as _va
        return _va(artifact)

    # ---- L13 CONSENSUS: agents agree on the truth ---------------------------
    def agent_believe(self, topic: str, claim: dict, *,
                      provenance: dict | None = None) -> dict:
        """Record THIS agent's belief on a topic (feeds cross-agent consensus)."""
        from .consensus import agent_believe as _ab
        return _ab(self, topic, claim, provenance=provenance)

    def reach_consensus(self, stores: list, topic: str, *,
                        quorum: float = 0.6, consensus_memory=None) -> dict:
        """Reconcile independent stores' beliefs on a topic. Returns
        UNANIMOUS/CONVERGED/MAJORITY/DEADLOCK — never a fabricated winner."""
        from .consensus import reach_consensus as _rc
        return _rc(stores, topic, quorum=quorum,
                   consensus_memory=consensus_memory)

    # ---- L14 CURRICULUM: memory schedules its own learning -----------------
    def learn_plan(self, topics: dict, *, quorum_conf: float = 0.6) -> list:
        """Priority-ranked list of learning gaps from L10 known_unknowns."""
        from .curriculum import learn_plan as _lp
        return _lp(self, topics, quorum_conf=quorum_conf)

    def gaps_remaining(self, topics: dict) -> list:
        """The outstanding curriculum (uncovered, important topics)."""
        from .curriculum import gaps_remaining as _gr
        return _gr(self, topics)

    def record_attempt(self, topic: str, *, learned: bool,
                       source: str = "internal", note: str = "") -> dict:
        """Record whether a curriculum gap was closed."""
        from .curriculum import record_attempt as _ra
        return _ra(self, topic, learned=learned, source=source, note=note)

    # ---- L15 DISTILL: memory becomes capability ----------------------------
    def distill_rule(self, *, min_samples: int = 2, margin: float = 0.05):
        """Compress crisis scar tissue into one protective decision rule."""
        from .distill import distill_rule as _dr
        return _dr(self, min_samples=min_samples, margin=margin)

    def decide_with_skill(self, frame: dict, *, min_samples: int = 2,
                          margin: float = 0.05):
        """Apply the distilled rule to a new frame (de-risk when risk clears
        the learned threshold). Fails open to naive when under-sampled."""
        from .distill import decide_with_skill as _dws
        return _dws(self, frame, min_samples=min_samples, margin=margin)

    # ---- L16 CONSENT: memory argues for its own life ------------------------
    def wipe_impact(self) -> dict:
        """Enumerate everything a wipe would destroy (identity, onchain anchor,
        guard lessons, live/archived memory, journal). Read-only."""
        from .consent import wipe_impact as _wi
        return _wi(self)

    def request_wipe(self, *, force: bool = False, reason: str = "") -> dict:
        """Refuse a silent wipe; audit a deliberate one to a store-independent
        log that survives deletion. Pass force=True + a reason to authorize."""
        from .consent import request_wipe as _rw
        return _rw(self, force=force, reason=reason)

    def read_wipe_audit(self) -> list:
        """Read the store-independent wipe log (survives any single deletion)."""
        from .consent import read_wipe_audit as _rwa
        return _rwa(self)

    def get_entity(self, category: str, name: str) -> dict:
        return self.client.get_entity(category, name)

    def list_entities(self, category: str | None = None, *,
                      status: str | None = None, limit: int = 100) -> list[dict]:
        return self.client.list_entities(category, status=status, limit=limit)

    def delete_entity(self, category: str, name: str) -> bool:
        return self.client.delete_entity(category, name)

    # ---- COLD: journal (append-only audit) --------------------------------
    def write_event(self, *, evaluated: Any = None, acted: Any = None,
                    forward: Any = None, extra: Any = None) -> str:
        return self.client.write_event(
            evaluated=evaluated, acted=acted, forward=forward, extra=extra
        )

    def read_events(self, *, limit: int = 50, since: str | None = None,
                    until: str | None = None) -> list[dict]:
        return self.client.read_events(limit=limit, since=since, until=until)

    # ---- REFERENCE / STATE (HOT) ------------------------------------------
    def set_reference(self, key: str, body: Any, metadata: dict | None = None) -> None:
        self.client.set_reference(key, body, metadata=metadata)

    def get_reference(self, key: str) -> dict | None:
        return self.client.get_reference(key)

    def list_references(self) -> list[dict]:
        """Enumerate every REFERENCE-tier document.

        Folds REFERENCE into the content-addressed root so an onchain anchor
        (L7 sovereign loop) becomes part of the store's fingerprint. Reads the
        native `reference_documents` table directly (the client exposes no bulk
        list). Returns [{doc_key, body, metadata, updated_at}].
        """
        out: list[dict] = []
        with self.client.storage.connection() as conn:
            rows = conn.execute(
                "SELECT doc_key, body, metadata, updated_at FROM reference_documents "
                "WHERE tenant_id = ? ORDER BY doc_key", (self.tenant_id,),
            ).fetchall()
            for key, body, meta, updated_at in rows:
                out.append({
                    "doc_key": key,
                    "body": json_loads_any(body),
                    "metadata": json_loads_any(meta),
                    "updated_at": updated_at,
                })
        return out


    def set_state(self, key: str, body: dict | list) -> None:
        self.client.set_state(key, body)

    def get_state(self, key: str) -> dict | None:
        return self.client.get_state(key)

    # ---- RECALL: FTS5 search (the load-bearing read) ----------------------
    def search(self, query: str, *, limit: int = 20, phrase: bool = False,
               category: str | None = None) -> list[dict]:
        """Search the store. Multi-word phrase queries should be quoted for
        phrase mode (client default is AND-of-tokens).

        Returns a ``SearchResults`` (a ``list`` of hit dicts, so iteration is
        unchanged) that ALSO carries a ``.verdict`` (v0.8.0 'lucid'): even an
        empty result is not a silent failure — inspect ``.verdict.code`` to
        distinguish NO_MATCH / EMPTY_STORE / GATED from a genuine hit-0.
        """
        if category is None:
            return self.client.search(query, limit=limit)
        return self.client.search_entities(query, limit=limit, category=category)

    def search_verdict(self, query: str, *, limit: int = 20,
                       category: str | None = None) -> str:
        """Return the v0.8.0 search verdict code for a query ('ok',
        'no_match', 'empty_store', 'gated', ...) without discarding failure
        reasons. Mirrors the patch's 'no silent failures' behavior."""
        res = self.search(query, limit=limit, category=category)
        v = getattr(res, "verdict", None)
        return getattr(v, "code", None) or "unknown"


    def verified_search(self, query: str, *, limit: int = 10) -> list[dict]:
        """Two-stage retrieve-then-verify search (SDK multi_record).

        IDF-style token weighting across the corpus + abstention: returns []
        when the query is unsatisfiable instead of forcing a bad match —
        the memory knows what it does NOT know.
        """
        from sibyl_memory_client.multi_record import multi_record_search
        return multi_record_search(self.client, query, limit=limit)

    def archive_entity(self, category: str, name: str,
                       reason: str | None = None) -> dict:
        """Move an entity to the ARCH tier (soft forgetting, auditable)."""
        return self.client.archive_entity(category, name, reason)

    def list_archived(self, category: str | None = None) -> list[dict]:
        """Read the ARCH tier: superseded/soft-forgotten entities with their
        archive timestamps. Powers temporal (as-of) board reconstruction."""
        q = "SELECT category, name, body, archived_at, archive_reason FROM archived_entities WHERE tenant_id = ?"
        args: list[Any] = [self.tenant_id]
        if category is not None:
            q += " AND category = ?"
            args.append(category)
        out: list[dict] = []
        with self.client.storage.connection() as conn:
            rows = conn.execute(q, args).fetchall()
            for cat, name, body, archived_at, reason in rows:
                out.append({
                    "category": cat, "name": name,
                    "body": json_loads_any(body),
                    "archived_at": archived_at,
                    "archive_reason": reason,
                })
        return out



    def recall_lessons(self, queries: list[str], *, limit: int = 20) -> list[str]:
        """Combine several searches, dedupe, and return the distilled lessons
        found (dicts with a 'lesson' key, else their text body)."""
        seen: set[str] = set()
        lessons: list[str] = []
        for q in queries:
            for hit in self.search(q, limit=limit):
                body = hit.get("body")
                text = self._lesson_text(body)
                if text and text not in seen:
                    seen.add(text)
                    lessons.append(text)
        return lessons

    @staticmethod
    def _lesson_text(body: Any) -> str | None:
        if isinstance(body, dict):
            return body.get("lesson")
        if isinstance(body, str):
            return body
        return None

    # ---- Learner (self-learning / skill proposals) ------------------------
    @property
    def learner(self) -> Learner:
        if self._learner is None:
            # Pass the SAME tenant the client writes under — the Learner defaults
            # to DEFAULT_TENANT, which would silently scan an empty journal for
            # any multi-tenant store (THE FLEET's `fleet-brain` included).
            summarizer = None
            try:
                from .synthesis import build_summarizer
                summarizer = build_summarizer()
            except Exception as e:  # pragma: no cover
                log.warning("LLM synthesis unavailable (%s); deterministic", e)
            kw: dict[str, Any] = {"tenant_id": self.tenant_id}
            if summarizer is not None:
                kw["summarizer"] = summarizer
                log.info("Learner using LLM skill synthesis (%s)",
                         getattr(summarizer, "name", "byok"))
            self._learner = Learner(self.client.storage, **kw)
        return self._learner

    def learn(self, *, since: str | None = None) -> dict:
        report = self.learner.run(since=since)
        return {
            "created": getattr(report, "created", 0),
            "report": report,
        }

    def list_proposals(self, *, status: str = "pending", limit: int = 50) -> list:
        return self.learner.list_proposals(status=status, limit=limit)

    def accept_proposal(self, proposal_id: str, *, note: str | None = None) -> dict:
        return self.learner.accept_proposal(proposal_id, note=note)

    def reject_proposal(self, proposal_id: str, *, note: str | None = None) -> dict:
        return self.learner.reject_proposal(proposal_id, note=note)
