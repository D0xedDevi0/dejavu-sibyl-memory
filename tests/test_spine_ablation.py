"""Test for the THE SPINE ablation benchmark — measured economic deletion gate."""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "..", "demo")


def test_spine_benchmark_runs_and_gate_holds():
    r = subprocess.run(
        [sys.executable, os.path.join(DEMO, "spine_ablation.py")],
        capture_output=True, text=True, cwd=os.path.join(HERE, ".."),
    )
    assert r.returncode == 0, r.stderr
    res = json.loads(r.stdout)
    assert res["crises"] >= 10
    # WITH memory must preserve materially more capital than the wiped store
    assert res["capital_preserved_multiple"] > 1.3
    assert res["capital_with_memory"] > res["capital_without_memory"]
    # memory de-risks (lower avg equity) and averts a meaningful loss
    assert res["avg_equity_memory"] < res["avg_equity_no_memory"]
    assert res["loss_averted_pp"] > 2.0
    # asset + identity claims
    assert res["asset_survived_all_crises"] is True
    assert res["identity_stable_all_crises"] is True
    assert res["identity_churn_without_memory"] == 1  # populated store -> new being


def test_spine_figure_is_valid_image():
    from PIL import Image
    p = os.path.join(DEMO, "spine_gate_figure.png")
    assert os.path.exists(p)
    img = Image.open(p)
    img.load()
    assert img.width >= 800 and img.height >= 500
