#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
OWNED_DIR=""
if [ "$#" -gt 0 ]; then
  DB="$1"
else
  OWNED_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sibyl-judge-gate.XXXXXX")
  DB="$OWNED_DIR/memory.db"
fi
cleanup() { if [ -n "$OWNED_DIR" ]; then rm -rf -- "$OWNED_DIR"; fi; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
PAUSE="${GATE_CAPTURE_DELAY:-0}"

# ---- pre-flight ------------------------------------------------------------
dirty() {
  if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
    echo "clean"
  else
    echo "dirty — uncommitted changes present"
  fi
}
beat() { if [ "$PAUSE" != "0" ]; then sleep "$PAUSE"; fi; }

# ---- banner (UTC timestamped, committed on) --------------------------------
clear 2>/dev/null || true
printf 'THE SPINE — CONTINUOUS UNEDITED SIBYL GATE\n'
printf 'UTC: '; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'GIT COMMIT: '; git rev-parse HEAD
printf 'WORKTREE: %s\n' "$(dirty)"
printf 'REPO: https://github.com/D0xedDevi0/dejavu-sibyl-memory\n'
printf 'PROCESS CONTRACT: every phase below is a separate Python process.\n'
printf 'DB: %s  (disposable — must not already exist)\n\n' "$DB"

# ---- guard: refuse to clobber an existing store ---------------------------
if [ -e "$DB" ] || [ -L "$DB" ]; then
  printf 'FATAL: DB exists — refusing to overwrite %s\n' "$DB" >&2
  printf '(pass a non-existent path or let mktemp supply one)\n' >&2
  exit 2
fi
# Explicit paths are never removed by this cleanup trap.

beat

# ---- PHASE 1: session A writes a real Sibyl lesson -------------------------
printf '$ SESSION A — write a real Sibyl lesson\n'
"$PY" demo/continuous_gate.py write --db "$DB"
beat

# ---- PHASE 2: session B, fresh process, cold-starts, recalls from Sibyl ----
printf '\n$ SESSION B — start a fresh process and recall from Sibyl\n'
recall_out=$("$PY" demo/continuous_gate.py recall --db "$DB" 2>&1)
printf '%s\n' "$recall_out"
beat

# ---- machine assertion: lessons MUST be found ------------------------------
if ! printf '%s' "$recall_out" | grep -qF 'lessons_found: 1'; then
  printf 'FATAL: memory-loaded recall did NOT find the lesson (gate broken)\n' >&2
  exit 3
fi
if ! printf '%s' "$recall_out" | grep -qE 'decision\.equity:\s+0\.0[0-9]+'; then
  printf 'FATAL: memory-loaded equity not de-risked (gate broken)\n' >&2
  exit 3
fi

# ---- PHASE 3: destructive control — delete the Sibyl store -----------------
printf '\n$ CONTROL — delete the same Sibyl store\n'
"$PY" demo/continuous_gate.py wipe --db "$DB"
beat

# ---- PHASE 4: session C, another fresh process, same frame, NO memory ------
printf '\n$ SESSION C — another fresh process, same frame, no memory\n'
wiped_out=$("$PY" demo/continuous_gate.py recall-wiped --db "$DB" 2>&1)
printf '%s\n' "$wiped_out"
beat

# ---- machine assertion: MUST be naive (no lessons, overweight equity) ------
if ! printf '%s' "$wiped_out" | grep -qF 'lessons_found: 0'; then
  printf 'FATAL: wiped recall found lessons (gate broken)\n' >&2
  exit 3
fi
if ! printf '%s' "$wiped_out" | grep -qF 'decision.equity: 0.55'; then
  printf 'FATAL: wiped recall not naive 0.55 (gate broken)\n' >&2
  exit 3
fi

# ---- verdict ---------------------------------------------------------------
printf '\nGATE RESULT: Sibyl present => equity <=0.05; Sibyl deleted => equity 0.55\n'
printf 'END UTC: '; date -u '+%Y-%m-%dT%H:%M:%SZ'
exit 0