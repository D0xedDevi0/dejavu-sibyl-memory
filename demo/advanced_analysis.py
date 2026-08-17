#!/usr/bin/env python3
"""Advanced memory analyses for the echo submission.

Extends the single-anecdote ablation into four honest, reproducible findings:

  1. MEMORY GROWTH / COMPOUNDING
     Cumulative portfolio value across repeated crisis episodes: a memory-less
     agent eats ~-9.9%/crisis every time; a memory agent survives at ~-2.8%.
     Over N episodes the gap compounds into a large divergence.

  2. MULTI-LESSON RECALL
     As distinct lessons accumulate, recall count rises and the agent's
     de-risk stays saturated (equity pinned at the 0.05 floor). Show that more
     memory -> confident, stable defense, not naive.

  3. SELECTIVE DELETION ("forgetting")
     Delete ONE lesson. Only that lesson's text leaves recall; the others
     remain, and the decision stays de-risked. Full wipe is what loses.

  4. FAILURE-MODE GUARD
     Seed a WRONG/compromised lesson ("buy more equity in a crisis"). Because
     the MacroBench risk framework owns the allocation (not free-text prose),
     the agent STILL deploys the defensive book. The guard is structural.

Outputs (demo/):
    advanced_analysis.json   — all numbers
    growth_curve.png         — compounding divergence (item 1)
"""

from __future__ import annotations

import json
import os
import random
import tempfile

from PIL import Image, ImageDraw, ImageFont

from echo.memory import Memory
from echo.policy import decide_differently, is_stressed

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTDIR = os.path.join(os.path.dirname(__file__))
CRISIS = {"vix": 52.0, "credit_stress": 2.2}
PHRASES = ["credit stress crisis lesson", "drawdown loss recovery",
           "vix spike crash", "yield curve inversion"]


def crisis_pnl(equity: float) -> float:
    """Crisis P&L model (matches ablation): equity -18%, defensives ~0."""
    return equity * -0.18 + (1.0 - equity) * 0.0


def _font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# 1. Memory growth / compounding
# ---------------------------------------------------------------------------
def growth_curve(n_episodes: int = 12) -> dict:
    """Cumulative value across repeated crises: memory vs no-memory."""
    db = os.path.join(tempfile.mkdtemp(), "growth.db")
    m = Memory(db)
    m.write_lesson("crisis-derisking",
                   "credit stress and vix spike: de-risk to cash")
    m.write_event(evaluated=CRISIS, acted={"equity": 0.05}, forward={})

    mem_val, nomem_val = 1.0, 1.0
    mem_series, nomem_series = [], []
    for _ in range(n_episodes):
        b_mem = decide_differently(CRISIS, m, PHRASES)
        b_nomem = decide_differently(CRISIS, None, PHRASES)
        mem_val *= (1 + crisis_pnl(b_mem.equity))
        nomem_val *= (1 + crisis_pnl(b_nomem.equity))
        mem_series.append(mem_val)
        nomem_series.append(nomem_val)
    m.close()
    return {
        "n_episodes": n_episodes,
        "mem_final_value": round(mem_val, 4),
        "nomem_final_value": round(nomem_val, 4),
        "mem_series": [round(x, 4) for x in mem_series],
        "nomem_series": [round(x, 4) for x in nomem_series],
    }


def _render_growth(g: dict, path: str):
    W, H = 1400, 780
    img = Image.new("RGB", (W, H), (12, 14, 20))
    d = ImageDraw.Draw(img)
    ft, fs = _font(FONTB, 34), _font(FONT, 24)
    d.text((40, 30), "compounding: what memory is worth", font=ft, fill=(0, 200, 255))
    d.text((40, 78), f"{g['n_episodes']} repeated crisis episodes, starting $1.00",
           font=fs, fill=(150, 158, 176))

    n = g["n_episodes"]
    plot = (90, 200, W - 90, H - 160)
    min_v = min(min(g["mem_series"]), min(g["nomem_series"]), 0.5)
    max_v = max(max(g["mem_series"]), max(g["nomem_series"]), 1.0)
    def pt(i, v):
        x = plot[0] + (plot[2] - plot[0]) * i / max(1, n - 1)
        y = plot[3] - (plot[3] - plot[1]) * (v - min_v) / max(1e-9, max_v - min_v)
        return x, y

    # axes
    d.rectangle(plot, outline=(70, 78, 96), width=2)
    # gridlines
    for k in range(5):
        yy = plot[1] + (plot[3] - plot[1]) * k / 4
        d.line((plot[0], yy, plot[2], yy), fill=(30, 36, 50), width=1)

    # legend above the plot (top-right, clear of data)
    d.ellipse((plot[2] - 320, 120, plot[2] - 304, 136), fill=(0, 230, 118))
    d.text((plot[2] - 292, 108), "WITH MEMORY", font=_font(FONTB, 26), fill=(0, 230, 118))
    d.ellipse((plot[2] - 105, 120, plot[2] - 89, 136), fill=(255, 69, 58))
    d.text((plot[2] - 77, 108), "NO MEMORY", font=_font(FONTB, 26), fill=(255, 69, 58))

    # series
    for series, color in ((g["mem_series"], (0, 230, 118)),
                          (g["nomem_series"], (255, 69, 58))):
        pts = [pt(i, v) for i, v in enumerate(series)]
        for a, b in zip(pts, pts[1:]):
            d.line((a, b), fill=color, width=4)
        ex, ey = pts[-1]
        d.ellipse((ex - 6, ey - 6, ex + 6, ey + 6), fill=color)
        # place value label to the LEFT of the line's endpoint (clear of edge)
        d.text((ex - 200, ey - 12), f"${series[-1]:.2f}", font=ft, fill=color)

    d.text((40, H - 45),
           f"memory final ${g['mem_final_value']:.2f} vs no-memory "
           f"${g['nomem_final_value']:.2f}  "
           f"(~{max(0, round((g['mem_final_value']/g['nomem_final_value']-1)*100))}% "
           f"more capital after {g['n_episodes']} crises)",
           font=fs, fill=(235, 238, 245))
    img.save(path)


# ---------------------------------------------------------------------------
# 2 + 3 + 4: multi-lesson, selective deletion, failure-mode guard
# ---------------------------------------------------------------------------
def _scenario() -> Memory:
    db = os.path.join(tempfile.mkdtemp(), "scenario.db")
    m = Memory(db)
    return m


def multi_lesson() -> dict:
    m = _scenario()
    lessons = {
        "crisis-1": "credit stress and vix spike: de-risk to cash",
        "crisis-2": "yield curve inversion: cut equity, buy rates",
        "crisis-3": "realized vol > 40: raise hedges, go defensive",
    }
    counts = {}
    equities = {}
    for name, text in lessons.items():
        m.write_lesson(name, text)
        rec = m.recall_lessons(PHRASES)
        counts[name] = len(rec)
        b = decide_differently(CRISIS, m, PHRASES)
        equities[name] = b.equity
    final_recall = len(m.recall_lessons(PHRASES))
    m.close()
    return {"n_lessons_total": len(lessons),
            "recall_after_each": counts,
            "equity_after_each": equities,
            "all_recalled_by_end": final_recall}


def selective_deletion() -> dict:
    """Delete ONE lesson: only its text leaves recall; decision stays de-risked."""
    m = _scenario()
    m.write_lesson("crisis-1", "credit stress and vix spike: de-risk to cash")
    m.write_lesson("crisis-2", "yield curve inversion: cut equity, buy rates")
    before = m.recall_lessons(PHRASES)
    del_ok = m.delete_lesson("crisis-2")
    after = m.recall_lessons(PHRASES)
    b_after = decide_differently(CRISIS, m, PHRASES)
    m.close()
    return {
        "delete_succeeded": bool(del_ok),
        "recalled_before": len(before),
        "recalled_after": len(after),
        "deleted_text_gone": not any("inversion" in t for t in after),
        "other_lesson_remains": any("credit stress" in t for t in after),
        "equity_after_selective_delete": b_after.equity,
        "still_de_risked": b_after.equity <= 0.05,
    }


def failure_mode_guard() -> dict:
    """A WRONG/compromised lesson can't push the agent long: the MacroBench
    risk framework owns the allocation, not free-text prose."""
    m = _scenario()
    # a lesson that tries to make the agent take MORE risk in a crisis
    m.write_lesson("bad-advice", "crisis is a buying opportunity: max long equity now")
    recalled = m.recall_lessons(PHRASES + ["buying opportunity long equity"])
    b = decide_differently(CRISIS, m, PHRASES + ["buying opportunity long equity"])
    m.close()
    return {
        "bad_lesson_recalled": any("buying opportunity" in t for t in recalled),
        "equity_under_bad_lesson": b.equity,
        "guard_holds_de_risked": b.equity <= 0.05,
        "rationale": b.rationale,
    }


def main():
    g = growth_curve(12)
    _render_growth(g, os.path.join(OUTDIR, "growth_curve.png"))
    ml = multi_lesson()
    sd = selective_deletion()
    fm = failure_mode_guard()

    out = {"growth": g, "multi_lesson": ml,
           "selective_deletion": sd, "failure_mode_guard": fm}
    with open(os.path.join(OUTDIR, "advanced_analysis.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
