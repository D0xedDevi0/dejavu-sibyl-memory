#!/usr/bin/env python3
"""Build the echo demo video — the fresh-session recall beat.

Renders terminal-style frames (PIL) from the REAL echo loop output and
assembles them with ffmpeg into an mp4. Two columns split-screen style:
    LEFT  — Session A learns (naive -> -18%, writes lesson)
    RIGHT — Session B cold-starts; WITH memory (recall -> de-risk) vs the
            SAME frame WITHOUT memory (wiped -> naive).

Produces demo/demo_video.mp4.
"""

import os, subprocess, textwrap, tempfile

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# Real output captured from the echo loop (verified live).
ABLATION = [
    "ABLATION BENCHMARK  (200 sampled frames, seed 1337)",
    "",
    "mean crisis return, NO MEMORY:   -9.90%",
    "mean crisis return, WITH MEMORY: -2.83%",
    "",
    "loss averted by remembering:     7.07pp",
    "trials where memory changed the decision: 75.0%",
    "",
    "> One anecdote. Now a measured claim.",
    "> Forgetting is a bug. Remembering is the strategy.",
]
# --------------------------------------------------------------------------
MEM_LEFT = [
    "SESSION A  --  fresh store",
    "",
    "frame: vix=52.0  credit_stress=2.2  (CRISIS)",
    "",
    "decide(frame): no recall yet ->",
    "  naive_book()",
    "  equity = 0.55   <-- stays LONG",
    "",
    "outcome: -18% drawdown",
    "",
    "write_lesson('crisis-derisking')",
    "write_event(journal)  -> Sibyl Memory",
    "",
    "> 'When stressed, de-risk to cash.'",
]

MEM_RIGHT = [
    "SESSION B  --  cold start (zero ctx)",
    "",
    "frame: vix=52.0  credit_stress=2.2  (SAME)",
    "",
    "recall: search('credit stress crisis')",
    "  -> 1 lesson FOUND  (from Session A)",
    "",
    "decide_differently(frame, memory)",
    "  de_risk_book()   <-- flips",
    "  equity = 0.05   cash = 0.59",
    "",
    "act_onchain(Base):  REAL TX",
    "  0x5175ae5a...  status 1  block 50108439",
    "",
    "echo: outcome written back -> compounds",
]

WIPED_RIGHT = [
    "SESSION B  --  store DELETED",
    "",
    "frame: vix=52.0  credit_stress=2.2  (SAME)",
    "",
    "recall: search(...)  ->  NO LESSONS",
    "  (memory.db wiped)",
    "",
    "decide_differently(frame, None)",
    "  naive_book()  <-- fails open",
    "  equity = 0.55   stays LONG",
    "",
    "outcome: -18% drawdown again.",
    "",
    "> That's what forgetting costs.",
]

TITLE = "echo  --  the agent that remembers"
SUB = "NEURAL_MESH x Sibyl Memory  |  forget => lose · remember => survive"

W, H = 1600, 900
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = (12, 14, 20)
PANEL = (18, 22, 32)
GREEN = (0, 230, 118)
RED = (255, 69, 58)
CYAN = (0, 200, 255)
GRAY = (150, 158, 176)
WHITE = (235, 238, 245)
AMBER = (255, 190, 60)

def load_font(path, size):
    return ImageFont.truetype(path, size)

def wrap_lines(lines, font, draw, max_w):
    out = []
    for line in lines:
        w = draw.textlength(line, font=font)
        if w <= max_w:
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width=max(20, int(max_w // (font.size * 0.6)))))
    return out

def render_frame(lines, *, left_title="SESSION A - LEARN", right_title="SESSION B - RECALL",
                 right_color=GREEN, tag=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f = load_font(FONT, 22)
    fb = load_font(FONTB, 30)
    ft = load_font(FONTB, 40)
    fs = load_font(FONT, 20)

    # header
    d.text((40, 28), TITLE, font=ft, fill=CYAN)
    d.text((40, 78), SUB, font=fs, fill=GRAY)
    # tag (top-right, e.g. "MEMORY-LOADED" / "STORE WIPED")
    if tag:
        tbox = d.textbbox((0, 0), tag, font=load_font(FONTB, 26))
        d.rectangle((W - tbox[2] - 70, 26, W - 30, 26 + tbox[3] + 16), fill=right_color)
        d.text((W - tbox[2] - 54, 38), tag, font=load_font(FONTB, 26), fill=(10, 10, 12))

    # panels
    pw = (W - 40 - 60) // 2   # two panels, 20 gap, margins
    px1, px2 = 30, 30 + pw + 20
    py, ph = 130, H - 130 - 40

    for px, title, col, ls in ((px1, left_title, GRAY, lines[0]),
                               (px2, right_title, right_color, lines[1])):
        d.rounded_rectangle((px, py, px + pw, py + ph), radius=14, fill=PANEL,
                            outline=right_color, width=2)
        d.text((px + 22, py + 18), title, font=fb, fill=col)
        y = py + 70
        for line in ls:
            col_l = WHITE
            if line.startswith(">"):
                col_l = AMBER
            elif "equity = 0.55" in line:
                col_l = RED
            elif "0.05" in line or "status 1" in line or "FOUND" in line:
                col_l = GREEN
            elif "de_risk" in line or "flips" in line:
                col_l = GREEN
            elif "NO LESSONS" in line or "wiped" in line or "forgetting" in line:
                col_l = RED
            d.text((px + 22, y), line, font=f, fill=col_l)
            y += 34

    # footer
    d.text((40, H - 36), "Hackathon demo  |  source: proto + src/echo  |  real Base txs",
           font=fs, fill=GRAY)
    return img

def save_gif_pairs(store, outdir, dur=0.5):
    """Render each line-pair as a frame -> PNGs for ffmpeg."""
    paths = []
    n = max(len(MEM_LEFT), len(MEM_RIGHT))
    for i in range(n):
        l = MEM_LEFT[i] if i < len(MEM_LEFT) else ""
        r = MEM_RIGHT[i] if i < len(MEM_RIGHT) else ""
        tag = "MEMORY-LOADED"
        img = render_frame(([l], [r]), right_color=GREEN, tag=tag)
        p = os.path.join(outdir, f"f{i:03d}.png")
        img.save(p)
        paths.append(p)
    return paths

def main():
    outdir = os.path.join(os.path.dirname(__file__), "_frames")
    os.makedirs(outdir, exist_ok=True)

    # Frame sequence for the ~30s recall beat (loaded path).
    frames = []
    seq = [
        ("SESSION A  learn", "SESSION B  recall", GREEN, "MEMORY-LOADED", 0),
    ]
    # Build a frame where left = learned, right = recalled (loaded), then wiped.
    img_loaded = render_frame((MEM_LEFT, MEM_RIGHT), right_color=GREEN, tag="MEMORY-LOADED")
    img_wiped = render_frame((MEM_LEFT, WIPED_RIGHT), right_color=RED, tag="STORE WIPED")
    p1 = os.path.join(outdir, "loaded.png"); img_loaded.save(p1)
    p2 = os.path.join(outdir, "wiped.png");  img_wiped.save(p2)
    frames = [p1, p2]

    # Ablation-closing frame (measured evidence).
    img_abl = render_frame((ABLATION[:9], ABLATION[9:]), right_color=CYAN,
                           tag="MEASURED")
    pa = os.path.join(outdir, "ablation.png"); img_abl.save(pa)

    # Title frame (first 3s).
    img_title = render_frame(([TITLE], [SUB]), right_color=CYAN)
    pt = os.path.join(outdir, "title.png"); img_title.save(pt)

    # Assemble: title 4s, loaded 8s, wiped 8s, loaded 8s, ablation 8s, title 3s.
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "4", "-i", pt,
        "-loop", "1", "-t", "8", "-i", p1,
        "-loop", "1", "-t", "8", "-i", p2,
        "-loop", "1", "-t", "8", "-i", p1,
        "-loop", "1", "-t", "8", "-i", pa,
        "-loop", "1", "-t", "3", "-i", pt,
        "-filter_complex",
        "[0][1][2][3][4][5]concat=n=6:v=1:a=0,format=yuv420p",
        "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart",
        os.path.join(os.path.dirname(__file__), "demo_video.mp4"),
    ]
    print("assembling demo_video.mp4 ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise SystemExit(r.returncode)
    out = os.path.join(os.path.dirname(__file__), "demo_video.mp4")
    print("DONE:", out, os.path.getsize(out), "bytes")

if __name__ == "__main__":
    main()
