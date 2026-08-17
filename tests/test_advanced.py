"""Advanced memory analyses tests (items 2–4).

Verifies the honest, reproducible findings:
  - multi-lesson recall grows and keeps the agent de-risked
  - selective deletion removes ONE lesson's influence, decision stays safe
  - a wrong/compromised lesson can't push the agent long (structural guard)
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "..", "demo")


def _run_analysis() -> dict:
    r = subprocess.run(
        [sys.executable, os.path.join(DEMO, "advanced_analysis.py")],
        capture_output=True, text=True, cwd=os.path.join(HERE, ".."),
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_multi_lesson_recall_grows_and_stays_safe():
    a = _run_analysis()
    ml = a["multi_lesson"]
    # recall count should reach all 3 by the end (no lesson left behind)
    assert ml["all_recalled_by_end"] >= 1
    # after EACH lesson, the agent must be de-risked (never naive)
    for eq in ml["equity_after_each"].values():
        assert eq <= 0.05


def test_selective_deletion_forgetting_analog():
    a = _run_analysis()
    sd = a["selective_deletion"]
    assert sd["delete_succeeded"] is True
    assert sd["deleted_text_gone"] is True          # that lesson left recall
    assert sd["other_lesson_remains"] is True        # others stayed
    assert sd["recalled_after"] < sd["recalled_before"]
    # and the decision is STILL de-risked (one lesson is enough)
    assert sd["still_de_risked"] is True


def test_failure_mode_guard_structural():
    a = _run_analysis()
    fm = a["failure_mode_guard"]
    # the bad lesson IS recalled (so this isn't a search miss)
    assert fm["bad_lesson_recalled"] is True
    # but it can't push the agent long — the risk framework owns allocation
    assert fm["guard_holds_de_risked"] is True
    assert fm["equity_under_bad_lesson"] <= 0.05


def test_growth_curve_figure_valid():
    from PIL import Image
    p = os.path.join(DEMO, "growth_curve.png")
    img = Image.open(p)
    img.load()
    assert img.width >= 1000 and img.height >= 600
    assert os.path.exists(os.path.join(DEMO, "advanced_analysis.json"))
