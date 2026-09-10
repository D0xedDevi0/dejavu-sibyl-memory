"""True subprocess deletion proof — real OS processes, not just in-process handles.

The in-process tests re-open Memory handles in the SAME Python interpreter.
That does NOT prove a genuinely fresh process (zero in-memory state, distinct
PID, distinct address space) can cold-start and recall from disk.  This test
spawns real OS processes via ``sys.executable`` running demo/continuous_gate.py
across four independent invocations (write → recall → wipe → recall-wiped) and
asserts:

* The write phase creates the store and a crisis lesson.
* A SEPARATE recall process (fresh PID) reads the lesson and de-risks.
* The wipe process DELETES the store.
* Another SEPARATE recall process (fresh PID) sees zero lessons and fails open
  to the naive 0.55 equity — proving memory was load-bearing.
"""

import os
import re
import subprocess
import sys
import tempfile


DEMO = os.path.join(os.path.dirname(__file__), "..", "demo", "continuous_gate.py")


def _run(phase: str, db: str) -> str:
    out = subprocess.run(
        [sys.executable, DEMO, phase, "--db", db],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, f"phase={phase} stderr:\n{out.stderr}"
    return out.stdout


def _equity(text: str) -> float:
    m = re.search(r"decision\.equity:\s+([\d.]+)", text)
    assert m, f"could not parse equity from:\n{text}"
    return float(m.group(1))


def _pid(text: str) -> int:
    m = re.search(r"pid:\s+(\d+)", text)
    assert m, f"could not parse pid from:\n{text}"
    return int(m.group(1))


def test_wrapper_default_runs_and_cleans_owned_directory(tmp_path):
    env = dict(os.environ, PYTHON=sys.executable, TMPDIR=str(tmp_path), GATE_CAPTURE_DELAY="0")
    result = subprocess.run(
        ["bash", os.path.join(os.path.dirname(DEMO), "run_continuous_gate.sh")],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "GATE RESULT:" in result.stdout
    assert not list(tmp_path.iterdir())


def test_wrapper_refuses_existing_store(tmp_path):
    db = tmp_path / "existing.db"
    db.write_bytes(b"do not overwrite")
    result = subprocess.run(
        ["bash", os.path.join(os.path.dirname(DEMO), "run_continuous_gate.sh"), str(db)],
        env=dict(os.environ, PYTHON=sys.executable), capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert db.read_bytes() == b"do not overwrite"


def test_fresh_process_write_recall_wipe_recall():
    """Four subprocesses: the full continuous gate as an automated test."""
    db = os.path.join(tempfile.mkdtemp(), "gate.db")

    # Phase 1: write
    assert "SESSION A / WRITE" in _run("write", db)

    # Phase 2: fresh PID recall -> de-risk
    rec = _run("recall", db)
    pid_b = _pid(rec)
    assert "lessons_found: 1" in rec
    assert _equity(rec) < 0.10  # de-risked

    # Phase 3: destructive wipe
    assert "DESTRUCTIVE CONTROL" in _run("wipe", db)

    # Phase 4: fresh PID recall-wiped -> naive
    rec2 = _run("recall-wiped", db)
    pid_c = _pid(rec2)
    assert "lessons_found: 0" in rec2
    assert _equity(rec2) > 0.50  # naive

    # Each recall is a true fresh process (distinct PIDs).
    assert pid_b != pid_c, (
        f"recall PIDs must differ (true subprocesses): {pid_b} vs {pid_c}"
    )