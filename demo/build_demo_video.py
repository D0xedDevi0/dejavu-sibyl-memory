#!/usr/bin/env python3
"""Build the dejavu demo video — D0xedDev × Sibyl fused, measured, cinematic.

Renders terminal-style frames (PIL) in the fused identity:
  · NEURAL_MESH blueprint navy + pixel-grid + cyan accents (#001240 / #0052FF / #00d4ff)
  · Sibyl oracle-terminal motif (sibyl@hackathon:~$ prompts, "Forgetting is a bug")
  · Real measured evidence (verified Base txs, ablation, six lanes, LoCoMo LLM judge)

Scenes:
  1  TITLE       — dejavu: the agent that remembers
  2  LEARN       — Session A naive → -18%, writes lesson to memory
  3  RECALL      — Session B WITH memory → de-risk, REAL Base tx (status 1)
  4  WIPED       — Session B store wiped → naive → -18% again (the deletion gate)
  5  ABLATION    — 200 frames, +7.07pp loss averted, 75% decisions changed
  6  LANES       — the six agentic-memory lanes NEURAL_MESH ships
  7  LOCOMO      — LoCoMo generative LLM judge (measured via Nous model path)
  8  CLOSE       — "Forgetting is a bug. Remembering is the strategy."

Produces demo/demo_video.mp4.
"""

import os, subprocess, textwrap, math, random

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# FUSED BRAND PALETTE  (NEURAL_MESH blueprint × Sibyl oracle)
BG      = (0, 18, 64)      # #001240 deep navy
BG2     = (0, 12, 40)      # deeper
PANEL   = (0, 30, 72)      # #001e48
GRID    = (0, 26, 90)      # pixel grid line
CYAN    = (0, 212, 255)    # #00d4ff
BLUE    = (0, 82, 255)     # #0052FF
GREEN   = (0, 255, 136)    # #00ff88
MAGENTA = (255, 0, 170)    # #ff00aa
RED     = (255, 69, 58)
AMBER   = (255, 190, 60)
WHITE   = (235, 240, 250)
GRAY    = (136, 153, 204)  # #8899cc
DIM     = (90, 108, 150)

W, H = 1600, 900
FONT    = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Real verified Base tx hashes (from README — status 1 on mainnet).
TX_DERISK   = "0x5175ae5a244b907753cacca9d529c87042ee11332c6e05cf4624d9016d4793dd"
TX_LEARN    = "0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a"

# Real measured evidence.
ABLATION = [
    "ABLATION BENCHMARK  (200 sampled frames · seed 1337)",
    "-----------------------------------------------------",
    "mean crisis return, NO MEMORY:    -9.90%",
    "mean crisis return, WITH MEMORY:  -2.83%",
    "",
    "loss averted by remembering:     +7.07pp",
    "trials where memory flipped the decision:  75.0%",
    "",
    "> one anecdote. now a measured claim.",
]
LANES = [
    "NEURAL_MESH  --  six agentic-memory lanes (real code)",
    "-----------------------------------------------------",
    "A  provenance-weighted   unverified 0.20 -> verified 0.95",
    "B  forgetting-as-feature  supersede -> zero stale truth",
    "C  pay-to-remember (x402) unpaid recall blocked",
    "D  memory -> LoRA data    distilled fine-tune examples",
    "E  prospective memory     intentions surface before due",
    "F  working-memory budget  token cap + priority eviction",
    "> 150 tests green. measured, not marketed.",
]
LOCOMO = [
    "LoCoMo END-TO-END  --  generative LLM judge (real)",
    "-----------------------------------------------------",
    "model: deepseek-v4-flash  (Hermes/Nous model path)",
    "n = 100  top_k = 5  mode: hybrid",
    "",
    "ctxR@5  0.120   EM@5 0.000   F1@5 0.041   MRR 0.068",
    "",
    "> the #1 roadmap item: executed, measured, honest.",
    "> pipeline unblocked - no external LLM credits needed.",
]

# Terminal "typed" lines per scene (sibyl@hackathon:~$ motif).
def prompt(lines, prompt="sibyl@hackathon:~$"):
    return [f"{prompt} {l}" if l and not l.startswith((">", "-")) else l for l in lines]

LEARN = prompt([
    "SESSION A  --  fresh store",
    "",
    "frame: vix=52.0 credit_stress=2.2  (CRISIS)",
    "",
    "decide(frame): no recall yet ->",
    "  naive_book()",
    "  equity = 0.55   <-- stays LONG",
    "",
    "outcome: -18% drawdown",
    "write_lesson('crisis-derisking')  -> memory",
    "write_event(journal)",
    "",
    "dejavu: 'when stressed, de-risk to cash.'",
])
RECALL = prompt([
    "SESSION B  --  cold start (zero conversation ctx)",
    "",
    "frame: vix=52.0 credit_stress=2.2  (SAME)",
    "",
    "recall: search('credit stress crisis')",
    "  -> 1 lesson FOUND  (from Session A)",
    "",
    "decide_differently(frame, memory)",
    "  de_risk_book()   <-- flips",
    "  equity = 0.05   cash = 0.59",
    "",
    "act_onchain(Base): REAL TX  status 1",
    "  block 50108439",
])
WIPED = prompt([
    "SESSION B  --  store DELETED",
    "",
    "frame: vix=52.0 credit_stress=2.2  (SAME)",
    "",
    "recall: search(...) ->  NO LESSONS",
    "  (memory wiped)",
    "",
    "decide_differently(frame, None)",
    "  naive_book()  <-- fails open",
    "  equity = 0.55   stays LONG",
    "",
    "outcome: -18% drawdown AGAIN.",
    "",
    "> that's what forgetting costs.",
])


def load_font(path, size):
    return ImageFont.truetype(path, size)


def pixel_grid(img, size=8, alpha=18):
    """Overlay a faint pixel grid + mesh node dots (NEURAL_MESH blueprint)."""
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, size):
        d.line([(x, 0), (x, H)], fill=GRID + (alpha,), width=1)
    for y in range(0, H, size):
        d.line([(0, y), (W, y)], fill=GRID + (alpha,), width=1)
    # faint node dots (mesh topology hint) — low opacity
    rnd = random.Random(7)
    for _ in range(60):
        x = rnd.randrange(0, W, 4)
        y = rnd.randrange(0, H, 4)
        c = (CYAN if rnd.random() < 0.5 else MAGENTA) + (26,)
        d.ellipse([x, y, x + 4, y + 4], fill=c)


def corner_marks(d):
    """Blueprint corner marker (BASED/NEURAL_MESH house mark)."""
    fs = load_font(FONTB, 16)
    d.text((W - 310, 24), "NEURAL_MESH x SIBYL", font=fs, fill=BLUE)
    fs2 = load_font(FONT, 14)
    d.text((W - 310, 46), "the agent that remembers", font=fs2, fill=DIM)


def render_frame(lines, *, title, right_title="", accent=CYAN, tag=None, prompt_mode=False):
    """Render one full terminal frame."""
    img = Image.new("RGB", (W, H), BG)
    pixel_grid(img)
    d = ImageDraw.Draw(img)
    f   = load_font(FONT, 24)
    fb  = load_font(FONTB, 30)
    ft  = load_font(FONTB, 44)
    fs  = load_font(FONT, 20)
    fsm = load_font(FONTB, 22)

    # header
    d.text((44, 34), "dejavu  --  the agent that remembers", font=ft, fill=CYAN)
    d.text((44, 96), "NEURAL_MESH x Sibyl Memory  |  forget => lose · remember => survive",
           font=fs, fill=GRAY)
    if tag:
        tbox = d.textbbox((0, 0), tag, font=fsm)
        d.rectangle((W - tbox[2] - 84, 34, W - 44, 34 + tbox[3] + 14), fill=accent)
        d.text((W - tbox[2] - 68, 46), tag, font=fsm, fill=BG)
    else:
        corner_marks(d)

    # main terminal panel
    pw = W - 44 - 44
    px, py = 44, 170
    ph = H - py - 60
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=14,
                        outline=BLUE, fill=PANEL, width=2)
    d.text((px + 24, py + 16), title, font=fb, fill=accent)
    y = py + 66
    for line in lines:
        col = WHITE
        if line.startswith(">"):
            col = AMBER
        elif "0.55" in line or "wiped" in line or "AGAIN" in line or "NO LESSONS" in line:
            col = RED
        elif "0.05" in line or "status 1" in line or "FOUND" in line or "de_risk" in line \
             or "flips" in line or "verified" in line or "0.95" in line or "green" in line:
            col = GREEN
        elif line.startswith("sibyl@") or ":" in line[:12]:
            col = CYAN
        elif line.startswith("A " ) or line.startswith("B ") or line.startswith("C ") \
             or line.startswith("D ") or line.startswith("E ") or line.startswith("F "):
            col = MAGENTA
        d.text((px + 28, y), line, font=f, fill=col)
        y += 40

    # footer (verified evidence)
    d.text((44, H - 36),
           "hackathon demo · src/dejavu · real Base txs verified on mainnet · all numbers measured",
           font=fs, fill=DIM)
    return img


def main():
    outdir = os.path.join(os.path.dirname(__file__), "_frames")
    os.makedirs(outdir, exist_ok=True)

    scenes = {
        "title":   render_frame(LEARN,  title="dejavu -- the agent that remembers", right_title="",
                                accent=CYAN),
        "learn":   render_frame(LEARN,  title="SESSION A  ·  learn (naive -> -18%)",
                                accent=RED,  tag="FRESH STORE"),
        "recall":  render_frame(RECALL, title="SESSION B  ·  recall (memory-loaded)",
                                accent=GREEN, tag="MEMORY-LOADED"),
        "wiped":   render_frame(WIPED,  title="SESSION B  ·  store DELETED (the gate)",
                                accent=RED,  tag="STORE WIPED"),
        "ablation":render_frame(ABLATION,title="measured evidence · ablation",
                                accent=CYAN, tag="MEASURED"),
        "lanes":   render_frame(LANES,  title="the six lanes NEURAL_MESH ships",
                                accent=MAGENTA, tag="REAL CODE"),
        "locomo":  render_frame(LOCOMO, title="LoCoMo end-to-end · LLM judge",
                                accent=GREEN, tag="UNBLOCKED"),
        "close":   render_frame(["> Forgetting is a bug.",
                                 "> Remembering is the strategy.",
                                 "",
                                 "dejavu · NEURAL_MESH · Sibyl Memory",
                                 "MIT · github.com/D0xedDevi0/NEURAL_MESH",
                                 "build in public · @D0xedDevi0"],
                                title="remember => survive",
                                accent=CYAN, tag="MIT"),
    }
    paths = {}
    for name, img in scenes.items():
        p = os.path.join(outdir, f"{name}.png")
        img.save(p)
        paths[name] = p

    # Assemble with ffmpeg — each scene a few seconds.
    durs = {"title": 5, "learn": 9, "recall": 9, "wiped": 9,
            "ablation": 9, "lanes": 10, "locomo": 9, "close": 6}
    cmd = ["ffmpeg", "-y"]
    for name in scenes:
        cmd += ["-loop", "1", "-t", str(durs[name]), "-i", paths[name]]
    n = len(scenes)
    concat = "".join(f"[{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p"
    cmd += ["-filter_complex", concat, "-r", "30", "-c:v", "libx264",
            "-preset", "medium", "-crf", "20", "-movflags", "+faststart",
            os.path.join(os.path.dirname(__file__), "demo_video.mp4")]
    print("assembling demo_video.mp4 ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:])
        raise SystemExit(r.returncode)
    out = os.path.join(os.path.dirname(__file__), "demo_video.mp4")
    print("DONE:", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
