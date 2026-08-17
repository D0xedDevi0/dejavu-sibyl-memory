"""Ablation benchmark test — the measured-evidence proof.

Verifies the benchmark harness produces the load-bearing signal: memory
materially reduces expected crisis loss vs. no memory, across many frames.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "..", "demo")


def test_benchmark_runs_and_memory_wins():
    """The ablation harness runs headless and reports memory beats no-memory."""
    r = subprocess.run(
        [sys.executable, os.path.join(DEMO, "ablation_benchmark.py")],
        capture_output=True, text=True, cwd=os.path.join(HERE, ".."),
    )
    assert r.returncode == 0, r.stderr
    results = json.loads(r.stdout)
    assert results["trials"] >= 100
    assert results["mean_return_memory_pct"] > results["mean_return_no_memory_pct"]
    # memory must avert a meaningful loss on average
    assert results["mean_loss_averted_pp"] > 2.0
    assert results["avg_equity_memory"] < results["avg_equity_no_memory"]
    # outputs written
    assert os.path.exists(os.path.join(DEMO, "ablation_results.json"))
    assert os.path.exists(os.path.join(DEMO, "ablation_figure.png"))


def test_figure_is_valid_image():
    from PIL import Image
    p = os.path.join(DEMO, "ablation_figure.png")
    img = Image.open(p)
    img.load()
    assert img.width >= 800 and img.height >= 500
