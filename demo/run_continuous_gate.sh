#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
DB="${1:-/tmp/sibyl-judge-gate.db}"
PAUSE="${GATE_CAPTURE_DELAY:-0}"
beat() { if [ "$PAUSE" != "0" ]; then sleep "$PAUSE"; fi; }
clear 2>/dev/null || true
printf 'THE SPINE — CONTINUOUS UNEDITED SIBYL GATE\n'
printf 'UTC: '; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'GIT COMMIT: '; git rev-parse HEAD
printf 'REPO: https://github.com/D0xedDevi0/dejavu-sibyl-memory\n'
printf 'PROCESS CONTRACT: every phase below is a separate Python process.\n\n'
beat
printf '$ SESSION A — write a real Sibyl lesson\n'
"$PY" demo/continuous_gate.py write --db "$DB"
beat
printf '\n$ SESSION B — start a fresh process and recall from Sibyl\n'
"$PY" demo/continuous_gate.py recall --db "$DB"
beat
printf '\n$ CONTROL — delete the same Sibyl store\n'
"$PY" demo/continuous_gate.py wipe --db "$DB"
beat
printf '\n$ SESSION C — another fresh process, same frame, no memory\n'
"$PY" demo/continuous_gate.py recall-wiped --db "$DB"
beat
printf '\nGATE RESULT: Sibyl present => equity <=0.05; Sibyl deleted => equity 0.55\n'
printf 'END UTC: '; date -u '+%Y-%m-%dT%H:%M:%SZ'
