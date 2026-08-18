#!/usr/bin/env python3
"""Ablation benchmark for the dejavu loop.

The pitch rests on ONE anecdote today. This turns it into a *measured claim*:
run the REAL `decide_differently` + Sibyl Memory across many randomly sampled
market frames, once WITH memory (lesson recalled) and once WITHOUT (store
deleted), apply the same crisis P&L model to the resulting book, and report:

    - mean portfolio return (memory vs no-memory)
    - % of trials where memory changed the decision
    - mean drawdown avoided / loss averted
    - a figure (PNG) for the README / demo

Outputs:
    demo/ablation_results.json  — the numbers
    demo/ablation_figure.png    — bar chart (returns: memory vs no-memory)
"""

from __future__ import annotations

import json
import os
import random
import tempfile

from PIL import Image, ImageDraw, ImageFont

from dejavu.memory import Memory
from dejavu.policy import decide_differently, is_stressed

N_TRIALS = 200
SEED = 1337
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTDIR = os.path.join(os.path.dirname(__file__))


def crisis_pnl(equity: float, *, crisis_equity_return: float = -0.18,
               defensive_equity_return: float = -0.03,
               rest_return: float = 0.0) -> float:
    """P&L for one crisis: equity carries the loss, defensives roughly flat."""
    return (equity * crisis_equity_return +
            (1.0 - equity) * rest_return)


def sample_frame(rng: random.Random) -> dict:
    """A plausible market frame spanning calm to full crisis."""
    calm = rng.random() < 0.25
    if calm:
        return {"vix": rng.uniform(10, 28), "credit_stress": rng.uniform(0.1, 0.6),
                "realized_vol": rng.uniform(8, 18), "yield_slope": rng.uniform(0.9, 1.8)}
    # stressed/crisis
    return {"vix": rng.uniform(30, 75), "credit_stress": rng.uniform(0.7, 3.0),
            "realized_vol": rng.uniform(20, 55), "yield_slope": rng.uniform(-0.4, 0.9)}


def main():
    rng = random.Random(SEED)

    # One store, one crisis lesson written once, then recalled per trial.
    db = os.path.join(tempfile.mkdtemp(), "ablate.db")
    m = Memory(db)
    m.write_lesson("crisis-derisking",
                   "When credit stress and vix spike together, de-risk to cash.")
    m.write_event(evaluated={"vix": 52.0, "credit_stress": 2.2},
                  acted={"equity": 0.55},
                  forward={"note": "stayed long through crisis, lost 18%"})
    phrases = ["credit stress crisis lesson", "drawdown loss recovery"]

    frames = [sample_frame(rng) for _ in range(N_TRIALS)]

    mem_ret, nomem_ret, changed = [], [], 0
    mem_eq, nomem_eq = [], []
    for f in frames:
        # WITH memory
        b_mem = decide_differently(f, m, phrases)
        mem_eq.append(b_mem.equity)
        mem_ret.append(crisis_pnl(b_mem.equity))
        # WITHOUT memory (store deleted)
        b_nomem = decide_differently(f, None, phrases)
        nomem_eq.append(b_nomem.equity)
        nomem_ret.append(crisis_pnl(b_nomem.equity))
        if abs(b_mem.equity - b_nomem.equity) > 1e-9:
            changed += 1
    m.close()

    mean_mem = sum(mem_ret) / N_TRIALS
    mean_nomem = sum(nomem_ret) / N_TRIALS
    averted = abs(mean_mem - mean_nomem) * 100  # percentage points
    avg_mem_eq = sum(mem_eq) / N_TRIALS
    avg_nomem_eq = sum(nomem_eq) / N_TRIALS
    n_stressed = sum(1 for f in frames if is_stressed(f))

    results = {
        "trials": N_TRIALS,
        "stressed_trials": n_stressed,
        "mean_return_memory_pct": round(mean_mem * 100, 3),
        "mean_return_no_memory_pct": round(mean_nomem * 100, 3),
        "mean_loss_averted_pp": round(averted, 3),
        "avg_equity_memory": round(avg_mem_eq, 3),
        "avg_equity_no_memory": round(avg_nomem_eq, 3),
        "pct_trials_decision_changed": round(changed / N_TRIALS * 100, 1),
        "model": {"crisis_equity_return": -0.18, "defensive_equity_return": -0.03,
                  "rest_return": 0.0},
    }
    with open(os.path.join(OUTDIR, "ablation_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    _render_figure(results, os.path.join(OUTDIR, "ablation_figure.png"))
    print(json.dumps(results, indent=2))


def _render_figure(r, path: str):
    W, H = 1280, 760
    img = Image.new("RGB", (W, H), (12, 14, 20))
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(FONTB, 34)
    fm = ImageFont.truetype(FONT, 26)
    fs = ImageFont.truetype(FONT, 24)

    d.text((40, 30), "dejavu ablation benchmark", font=ft, fill=(0, 200, 255))
    d.text((40, 76), f"mean crisis return  ·  {r['trials']} frames  ·  seed 1337",
           font=fs, fill=(150, 158, 176))

    # ---- bars: both returns are negative, extend LEFT from a common baseline.
    # Map return pct in [-0.05, 0] -> x in [right_of_axis, axis].
    axis_x = 980
    bar_h = 120
    y_no, y_mem = 240, 420
    # absolute worst value determines scale so both bars fit with 80px margin.
    worst = max(abs(r["mean_return_no_memory_pct"] / 100),
                abs(r["mean_return_memory_pct"] / 100))
    scale = (axis_x - 120) / worst   # px per unit return

    for pct, y, color, label in (
        (r["mean_return_no_memory_pct"], y_no, (255, 69, 58), "NO MEMORY"),
        (r["mean_return_memory_pct"], y_mem, (0, 230, 118), "WITH MEMORY"),
    ):
        w = abs(pct / 100) * scale
        x0 = axis_x - w
        d.rounded_rectangle((x0, y, axis_x, y + bar_h), radius=10, fill=color)
        # label + value stacked on the right of the axis (never clipped).
        d.text((axis_x + 20, y + 20), label, font=ft, fill=color)
        val_txt = f"{pct:.2f}%"
        d.text((axis_x + 20, y + 70), val_txt, font=fm, fill=color)

    # axis / zero line
    d.line((axis_x, 150, axis_x, H - 100), fill=(70, 78, 96), width=2)
    d.text((axis_x - 60, 150), "0", font=fs, fill=(120, 128, 148))

    # stats block
    d.text((40, H - 70),
           f"loss averted: {r['mean_loss_averted_pp']}pp  ·  "
           f"decision changed: {r['pct_trials_decision_changed']}%  ·  "
           f"avg equity: mem {r['avg_equity_memory']} vs no-mem "
           f"{r['avg_equity_no_memory']}", font=fs, fill=(235, 238, 245))
    img.save(path)


if __name__ == "__main__":
    main()
