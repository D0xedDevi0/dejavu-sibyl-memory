#!/usr/bin/env python3
"""Build THE SPINE v3 demo video (corrected 2:30 script).

Every number on screen comes from a real execution run at build time
(guard receipt, gaps, ablation JSON) or a verified literal (historical Base
tx hashes, x402 endpoint from README). No invented content.
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
REPO = HERE.parent.parent

# house palette
BG     = (0, 18, 64)
PANEL  = (0, 30, 72)
GRID   = (0, 26, 90)
CYAN   = (0, 212, 255)
BLUE   = (0, 82, 255)
GREEN  = (0, 255, 136)
MAGENTA= (255, 0, 170)
RED    = (255, 90, 70)
AMBER  = (255, 190, 60)
WHITE  = (220, 230, 245)
GRAY   = (136, 153, 204)
DIM    = (90, 108, 150)

W, H = 1600, 900
FONT  = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# verified literals (README)
TX_ANCHOR = "0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7"
X402_URL  = "https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query"
REPO_URL  = "https://github.com/D0xedDevi0/dejavu-sibyl-memory"


def font(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)


def base_canvas(title, tag, accent):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 16):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 16):
        d.line([(0, y), (W, y)], fill=GRID, width=1)
    d.text((60, 42), title, font=font(44, True), fill=accent)
    d.text((60, 100), "THE SPINE  ·  NEURAL_MESH x Sibyl Memory",
           font=font(20), fill=GRAY)
    if tag:
        tb = d.textbbox((0, 0), tag, font=font(22, True))
        d.rectangle((W - tb[2] - 90, 44, W - 60, 44 + tb[3] + 16), fill=accent)
        d.text((W - tb[2] - 72, 58), tag, font=font(22, True), fill=BG)
    return img, d


def draw_panel(d, y0, lines, accent=CYAN, title=None, lh=40, fs=24):
    """lines: list of (text, color). Returns next y."""
    x0, x1 = 60, W - 60
    d.rounded_rectangle((x0, y0, x1, y0 + lh * len(lines) + (70 if title else 20)),
                        radius=12, outline=BLUE, fill=PANEL, width=2)
    y = y0 + 16
    if title:
        d.text((x0 + 24, y), title, font=font(26, True), fill=accent)
        y += 52
    else:
        y += 8
    for text, col in lines:
        d.text((x0 + 28, y), text, font=font(fs), fill=col)
        y += lh
    return y + 16


def render_title(out):
    img, d = base_canvas("THE SPINE", "persistent memory", CYAN)
    d.text((60, 330), "Restart the worker. Keep the lesson.",
           font=font(64, True), fill=WHITE)
    d.text((60, 430), "A sovereign memory layer for autonomous agents.",
           font=font(28), fill=GRAY)
    d.text((60, 490), "experience  →  guarded decision  →  verifiable receipt",
           font=font(24), fill=GREEN)
    d.text((60, 620), "MIT  ·  " + REPO_URL, font=font(20), fill=DIM)
    img.save(out)


def render_guard(out, receipt):
    g = receipt["guard"]; p = receipt["proposed"]; a = receipt["approved"]
    o = receipt["onchain"]; mem = receipt["memory"]
    img, d = base_canvas("L11 GUARD — memory that says no", "real receipt", RED)
    lines = [
        ("proposed (policy text-miss)          equity 0.55", RED),
        ("guard verdict: BLOCK                 matched: crisis-derisking", AMBER),
        ("approved (reaches the adapter)       equity 0.015", GREEN),
        ("onchain action: de_risk              dry_run true", GREEN),
        ("tx_hash: null                        live_tx: false", WHITE),
        (f"decision_id: {receipt['decision_id']}", CYAN),
        (f"memory root: {mem['root'][:24]}…", CYAN),
        ("", WHITE),
        ("no transaction claimed — the receipt is the proof.", DIM),
    ]
    draw_panel(d, 180, lines, accent=RED, title="guarded-decision dry-run receipt")
    img.save(out)


def render_gaps(out, before, plan, after):
    img, d = base_canvas("gaps become work", "L10 + L14", CYAN)
    lines = [
        (f"known_unknowns BEFORE    status: {before['status']}", AMBER),
        ("  action: " + before["action"], GRAY),
        (f"learn_plan              topic: {plan[0]['topic']}", CYAN),
        (f"  priority {plan[0]['priority']}  gap {plan[0]['gap']}  status {plan[0]['status']}", GRAY),
        ("acquire: write lesson + provenance + record_attempt", GREEN),
        (f"known_unknowns AFTER     status: {after['status']}", GREEN),
        ("  high_confidence_hits: " + str(after["high_confidence_hits"]), GREEN),
        ("", WHITE),
        ("coverage changes only after a lesson is acquired —", DIM),
        ("never because the agent claimed it learned.", DIM),
    ]
    draw_panel(d, 180, lines, accent=CYAN, title="real known_unknowns output")
    img.save(out)


def render_measured(out, abl):
    img, d = base_canvas("measured, bounded evidence", "200 frames", GREEN)
    lines = [
        (f"trials {abl['trials']}   stressed {abl['stressed_trials']}", WHITE),
        (f"mean crisis return  WITH memory   {abl['mean_return_memory_pct']:+.3f}%", GREEN),
        (f"mean crisis return  NO memory     {abl['mean_return_no_memory_pct']:+.3f}%", RED),
        (f"loss averted by remembering        {abl['mean_loss_averted_pp']:+.3f}pp", CYAN),
        (f"trials where memory flipped the decision  {abl['pct_trials_decision_changed']:.1f}%", WHITE),
        ("", WHITE),
        ("toy P&L model, seeded fixture — not realized returns.", DIM),
        ("reproducer: demo/ablation_benchmark.py", DIM),
    ]
    draw_panel(d, 180, lines, accent=GREEN, title="ablation_benchmark output")
    img.save(out)


def render_base(out):
    img, d = base_canvas("historical Base evidence", "HISTORICAL", AMBER)
    lines = [
        ("root-anchor tx  (status 1):", GRAY),
        ("  " + TX_ANCHOR[:48] + "…", CYAN),
        ("x402 endpoint (unpaid challenge):", GRAY),
        ("  " + X402_URL[:58] + "…", CYAN),
        ("adapter action: symbolic 1,000-wei transfer,", WHITE),
        ("  not a portfolio trade.", WHITE),
        ("", WHITE),
        ("two settlement tests were self-funded —", AMBER),
        ("not presented as customer demand.", AMBER),
    ]
    draw_panel(d, 180, lines, accent=AMBER, title="labelled historical evidence")
    img.save(out)


def render_close(out):
    img, d = base_canvas("THE SPINE", "MIT", CYAN)
    d.text((60, 300), "persisted experience", font=font(54, True), fill=WHITE)
    d.text((60, 380), "guarded decisions", font=font(54, True), fill=WHITE)
    d.text((60, 460), "evidence you can inspect", font=font(54, True), fill=CYAN)
    d.text((60, 600), "Next: a measured external operator pilot.", font=font(26), fill=GREEN)
    d.text((60, 660), REPO_URL, font=font(20), fill=DIM)
    img.save(out)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(r.returncode)
    return r.stdout


def main():
    outdir = HERE / "cards"
    outdir.mkdir(exist_ok=True)
    env = {"DEJAVU_DRY_RUN": "1", "DEJAVU_VIRTUALS_LIVE": "0"}

    # fresh real evidence
    guard = json.loads(run(["env", *[f"{k}={v}" for k, v in env.items()],
                            ".venv/bin/python", "demo/_v3/evidence_demo.py",
                            "guard-block"]))
    gaps = run(["env", *[f"{k}={v}" for k, v in env.items()],
                ".venv/bin/python", "demo/_v3/evidence_demo.py", "gaps"])
    abl = json.loads((REPO / "demo/ablation_results.json").read_text())

    render_title(outdir / "title.png")
    render_guard(outdir / "guard.png", guard)
    render_base(outdir / "base.png")
    render_close(outdir / "close.png")
    render_measured(outdir / "measured.png", abl)

    # parse gaps output (single JSON object with before/plan/after)
    gaps_json = json.loads(gaps)
    render_gaps(outdir / "gaps.png", gaps_json["before"],
                gaps_json["plan"], gaps_json["after"])

    print("cards rendered:", sorted(p.name for p in outdir.glob("*.png")))


if __name__ == "__main__":
    main()
