"""NEURAL_MESH backend for the dejavu loop — Lane E (unify the two tracks).

Implements the SAME `Memory` interface the dejavu agent uses with Sibyl
(`write_lesson` / `recall_lessons` / `delete_lesson` / `delete_store`), but
backed by the real NEURAL_MESH agentic-memory mesh.

Why this matters: the hackathon entry proves a *memory-driven* dejavu agent with
the deletion gate (recalled crisis lesson changes allocation; wipe it and the
agent reverts to naive). That proof should not depend on one memory engine.
This backend lets the SAME demo run on NEURAL_MESH — the production
self-organizing / self-forgetting mesh — so the deletion-gate thesis is shown
on two independent implementations. One story, two tracks.

Usage (identical to the Sibyl Memory):
    from dejavu.mesh_backend import MeshMemory as Memory
    mem = Memory(":memory:")
    mem.write_lesson("crisis-1", "de-risk to <=5% equity when VIX spikes", frame=...)
    lessons = mem.recall_lessons(["crisis VIX equity de-risk"])
    mem.delete_lesson("crisis-1")   # selective forgetting
    mem.delete_store()               # the deletion gate

The NEURAL_MESH backend is OPTIONAL. It needs the sibling repo at
github.com/BasedNUKEM/NEURAL_MESH (set NEURAL_MESH_ROOT to point at it).
If that repo isn't importable, this module still imports cleanly and
`MeshMemory` raises an informative ImportError on construction — so a clean
checkout of THIS repo installs and runs without it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Make the NEURAL_MESH package importable (it lives in a sibling repo).
_NEURAL_MESH_ROOT = os.environ.get(
    "NEURAL_MESH_ROOT", "/opt/data/NEURAL_MESH"
)
if _NEURAL_MESH_ROOT not in sys.path:
    sys.path.insert(0, _NEURAL_MESH_ROOT)

try:
    from neural_mesh import Mesh, MemoryType  # noqa: E402
    from neural_mesh.prospective import upcoming  # noqa: E402
    _NEURAL_MESH_AVAILABLE = True
except ImportError:  # pragma: no cover - CI / clean checkout without sibling repo
    _NEURAL_MESH_AVAILABLE = False

LESSON_CATEGORY = "lesson"


if _NEURAL_MESH_AVAILABLE:
    class MeshMemory:
        """NEURAL_MESH-backed store exposing the dejavu `Memory` interface."""

        def __init__(self, db_path: str | Path = ":memory:", *, tenant_id: str | None = None):
            # db_path kept for interface parity; NEURAL_MESH uses its own SQLite.
            self._mesh = Mesh(str(db_path) if str(db_path) != ":memory:" else ":memory:")
            self._tenant = tenant_id
            # memory-type split: lessons are semantic (facts), frames are episodic
            self._lessons: dict[str, str] = {}
            self._node_ids: dict[str, str] = {}

        # ---- lifecycle ----------------------------------------------------
        def close(self) -> None:
            # NEURAL_MESH keeps no open handle to release; provided for parity.
            return None

        @property
        def exists(self) -> bool:
            return bool(self._lessons) or len(self._mesh._load()) > 0

        def delete_store(self) -> None:
            """Wipe the whole mesh — the deletion gate. A wiped mesh is a fresh,
            memory-less store (the honest equivalent of 'erase everything')."""
            self._lessons.clear()
            self._mesh = Mesh(":memory:")

        # ---- WARM: lessons ------------------------------------------------
        def write_lesson(self, name: str, lesson: str, *, frame: dict | None = None,
                         outcome: dict | None = None, status: str = "active") -> dict:
            self._lessons[name] = lesson
            meta: dict[str, Any] = {"category": LESSON_CATEGORY, "name": name}
            if frame is not None:
                meta["frame"] = frame
            if outcome is not None:
                meta["outcome"] = outcome
            node = self._mesh.add(lesson, type=MemoryType.SEMANTIC, lane="cold",
                                  provenance="dejavu-crisis", trust=0.95, meta=meta)
            self._node_ids[name] = node.id
            return {"name": name, "node_id": node.id, "status": status}

        def get_lesson(self, name: str) -> dict:
            lesson = self._lessons.get(name)
            if lesson is None:
                return {}
            return {"name": name, "lesson": lesson, "status": "active"}

        def delete_lesson(self, name: str) -> bool:
            """Selective forgetting: drop the lesson AND retire its mesh node so
            recall can no longer surface it (NEURAL_MESH's `superseded_by` gate)."""
            if name not in self._lessons:
                return False
            del self._lessons[name]
            nid = self._node_ids.pop(name, None)
            if nid is not None:
                node = self._mesh._load().get(nid)
                if node is not None:
                    node.superseded_by = "__forgotten__"
                    self._mesh._save(node)
                    self._mesh._invalidate_cache()
            return True

        def list_lessons(self, *, status: str | None = None, limit: int = 100) -> list[dict]:
            return [{"name": k, "lesson": v, "status": "active"}
                    for k, v in list(self._lessons.items())[:limit]]

        # ---- recall (the load-bearing read) ------------------------------
        def search(self, query: str, *, limit: int = 20, phrase: bool = False,
                   category: str | None = None) -> list[dict]:
            nodes = self._mesh.recall(query, top_k=limit)
            return [{"body": {"lesson": n.content}, "content": n.content}
                    for n in nodes]

        def recall_lessons(self, queries: list[str], *, limit: int = 20) -> list[str]:
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

        # ---- Sibyl-only surface kept as no-ops / light so the interface matches
        def write_event(self, *, evaluated=None, acted=None, forward=None,
                        extra=None) -> str:
            self._mesh.add(f"event eval={evaluated} act={acted}",
                           type=MemoryType.EPISODIC, lane="hot",
                           provenance="dejavu-loop")
            return "mesh-event"

        def read_events(self, *, limit: int = 50, since=None, until=None) -> list[dict]:
            nodes = list(self._mesh._load().values())[:limit]
            return [{"content": n.content} for n in nodes]

        def set_reference(self, key: str, body: Any, metadata: dict | None = None) -> None:
            self._mesh.add(f"{key}: {body}", type=MemoryType.SEMANTIC, lane="hot",
                           provenance="reference")

        def get_reference(self, key: str) -> dict | None:
            return None

        def set_state(self, key: str, body) -> None:
            pass

        def get_state(self, key: str):
            return None

        # ---- Learner surface (no-op; NEURAL_MESH does DREAM/LoRA instead) -----
        @property
        def learner(self):
            return None

        def learn(self, *, since=None) -> dict:
            return {"created": 0, "report": None}

else:  # pragma: no cover
    class MeshMemory:  # type: ignore[no-redef]
        """Placeholder when the optional NEURAL_MESH sibling repo is absent.

        Constructing it raises an informative error; the core dejavu agent and
        its tests never touch this module, so a clean checkout still works.
        """

        def __init__(self, *a, **k):
            raise ImportError(
                "NEURAL_MESH not importable. This optional backend needs the "
                "sibling repo at github.com/BasedNUKEM/NEURAL_MESH (or set "
                "NEURAL_MESH_ROOT). The core dejavu agent does not require it."
            )
