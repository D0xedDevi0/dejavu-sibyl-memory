"""Lane E — the deletion gate runs identically on the NEURAL_MESH backend.

This is the unifying proof: the same memory-dejavu crisis demo that the hackathon
entry proves on Sibyl also runs on NEURAL_MESH (the production self-organizing
/ self-forgetting agentic-memory mesh). Same interface, same decision, same
deletion-gate asymmetry:

  - WITH memory (mesh intact)  -> recall -> de-risk (equity <= 0.05)
  - WIPED mesh                 -> no recall -> naive (equity > 0.5)

Run:  pytest tests/test_mesh_backend.py -v
"""
import os
import tempfile

from dejavu.agent import LESSON_NAME, session_a, session_b
from dejavu.mesh_backend import MeshMemory


def _crisis_frame():
    return {"vix": 52.0, "credit_stress": 2.2}


def test_mesh_with_memory_recalls_and_de_risks():
    """NEURAL_MESH-backed store intact -> session B recalls + de-risks."""
    mem = MeshMemory(":memory:")
    crisis = _crisis_frame()

    session_a(mem, crisis)   # writes the lesson into the mesh
    book = session_b(mem, crisis)

    assert book.equity <= 0.05, \
        f"mesh-loaded agent should de-risk, got equity={book.equity}"
    mem.close()


def test_mesh_without_memory_fails_open_to_naive():
    """Fresh empty mesh -> no recall -> naive long-equity (the losing call)."""
    mem = MeshMemory(":memory:")
    crisis = _crisis_frame()
    book = session_b(mem, crisis)
    assert book.equity > 0.5, \
        f"mesh-less agent should stay long equity, got equity={book.equity}"
    mem.close()


def test_mesh_delete_store_breaks_behavior():
    """The judge's exact check, on the mesh: learn in A, WIPE the mesh, cold
    start B -> different (worse) decision. Memory is load-bearing on both
    implementations, not decorative."""
    mem = MeshMemory(":memory:")
    crisis = _crisis_frame()

    session_a(mem, crisis)    # learns
    mem.delete_store()        # wipe the mesh (the deletion gate)

    book = session_b(mem, crisis)
    assert book.equity > 0.5, \
        "after mesh wipe the agent must regress to naive"
    mem.close()


def test_mesh_loaded_vs_naive_differ_on_same_frame():
    """Same frame, mesh vs no-mesh -> decisions must diverge."""
    crisis = _crisis_frame()

    loaded = MeshMemory(":memory:")
    session_a(loaded, crisis)
    loaded_book = session_b(loaded, crisis)
    loaded.close()

    naive = MeshMemory(":memory:")
    naive_book = session_b(naive, crisis)
    naive.close()

    assert loaded_book.equity < naive_book.equity, \
        f"mesh memory should de-risk (eq={loaded_book.equity}) below " \
        f"naive (eq={naive_book.equity})"


def test_mesh_backend_supports_selective_forgetting():
    """delete_lesson removes ONE lesson's influence, leaving others."""
    mem = MeshMemory(":memory:")
    mem.write_lesson("crisis-1", "de-risk to <=5% equity when VIX spikes")
    mem.write_lesson("crisis-2", "raise cash when credit stress climbs")
    assert len(mem.list_lessons()) == 2
    assert mem.delete_lesson("crisis-1") is True
    lessons = mem.recall_lessons(["crisis credit stress cash"])
    assert any("credit stress" in l for l in lessons)
    assert not any("VIX" in l for l in lessons)
    mem.close()


def test_mesh_backend_imports_and_constructs():
    """The bridge imports cleanly and exposes the dejavu Memory surface."""
    mem = MeshMemory(":memory:")
    for attr in ("write_lesson", "recall_lessons", "delete_lesson",
                 "delete_store", "write_event", "search"):
        assert hasattr(mem, attr), f"missing {attr}"
    mem.close()
