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

    def set_state(self, key: str, body: dict | list) -> None:
        self.client.set_state(key, body)

    def get_state(self, key: str) -> dict | None:
        return self.client.get_state(key)

    # ---- RECALL: FTS5 search (the load-bearing read) ----------------------
    def search(self, query: str, *, limit: int = 20, phrase: bool = False,
               category: str | None = None) -> list[dict]:
        """Search the store. Multi-word phrase queries should be quoted for
        phrase mode (client default is AND-of-tokens)."""
        if category is None:
            return self.client.search(query, limit=limit)
        return self.client.search_entities(query, limit=limit, category=category)

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
