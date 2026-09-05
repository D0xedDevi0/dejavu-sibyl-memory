"""Test for the CONSCIENCE ablation — proof the second act (L9-L16) is
load-bearing ON TOP OF intact first-act memory (L1-L8).

Where spine_ablation.py proves "some memory beats a wiped store", this proves
the harder, sharper claim #4 targets: holding stored content IDENTICAL, the
agent with its conscience layers (L11 GUARD + L15 DISTILL) survives crises that
first-act recall is structurally blind to (realized-vol / curve-inversion
channels that is_stressed() never reads). FULL > ACT-ONE > NO-MEMORY.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "..", "demo")


def _run():
    r = subprocess.run(
        [sys.executable, os.path.join(DEMO, "conscience_ablation.py")],
        capture_output=True, text=True, cwd=os.path.join(HERE, ".."),
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_conscience_gradient_full_gt_actone_gt_nomem():
    res = _run()
    caps = res["capital"]
    # the whole thesis in one line: FULL beats ACT-ONE beats NO-MEMORY
    assert caps["full"] > caps["act-one"] > caps["no-memory"], caps
    # the conscience-specific delta is material, not a rounding artifact
    assert res["headlines"]["full_vs_act_one_multiple"] > 1.2
    assert res["headlines"]["act_one_vs_no_memory_multiple"] > 1.2
    assert res["headlines"]["full_vs_no_memory_multiple"] > res["headlines"][
        "act_one_vs_no_memory_multiple"]


def test_conscience_catches_every_recall_blind_novel_crisis():
    res = _run()
    hl = res["headlines"]
    # every novel-channel crisis (invisible to is_stressed / raw recall) must be
    # caught by a conscience layer — otherwise the second act isn't load-bearing.
    assert hl["novel_episodes"] >= 2
    assert hl["conscience_caught_novel"] == hl["novel_episodes"]
    # on those episodes, act-one is as blind as no-memory while full de-risks
    novel = [e for e in res["episodes"] if e["kind"] == "novel"]
    assert novel, "panel must contain recall-blind episodes"
    for e in novel:
        assert e["binding"] == "distill", e
        assert e["equity"]["full"] <= 0.05, e          # conscience floor
        assert e["equity"]["act-one"] >= 0.5, e        # recall blind -> naive
        assert e["recall_stressed"] is False, e        # truly below the trigger


def test_guard_is_backstop_when_store_too_thin_to_distill():
    res = _run()
    gc = res["headlines"]["guard_case"]
    # one hard lesson, no distilled rule (under-sampled) -> guard still vetoes
    assert gc["distill_rule_learned"] is False
    assert gc["guard_verdict"] == "block"
    assert gc["guard_equity"] <= 0.05
    assert gc["equity_saved"] >= 0.4


def test_figure_is_valid_image_and_outputs_written():
    _run()
    from PIL import Image
    p = os.path.join(DEMO, "conscience_gate_figure.png")
    assert os.path.exists(p)
    assert os.path.exists(os.path.join(DEMO, "conscience_ablation.json"))
    img = Image.open(p)
    img.load()
    assert img.width >= 800 and img.height >= 500
