#!/usr/bin/env python3
"""Render a captured PTY cast (real stdout + real timing) to a terminal video.

Faithful replay: actual output, actual timing, ANSI handled, blinking block
cursor as the only non-content affordance (standard terminal behavior — not
fabricated text). Output: PNG frames + ffmpeg assembly to MP4.
"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# House palette (NEURAL_MESH blueprint x Sibyl oracle)
BG      = (0, 18, 64)
TERM_BG = (4, 10, 28)
TITLEBG = (0, 30, 72)
CYAN    = (0, 212, 255)
BLUE    = (0, 82, 255)
GREEN   = (0, 255, 136)
AMBER   = (255, 190, 60)
RED     = (255, 100, 90)
WHITE   = (220, 230, 245)
GRAY    = (120, 138, 178)
DIM     = (70, 84, 120)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class Term:
    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.grid = [[" "] * cols for _ in range(rows)]
        self.r = self.c = 0

    def write(self, text):
        # strip ANSI SGR color (keep other CSI like clear/cursor)
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "\x1b":
                m = CSI_RE.match(text, i)
                if not m:
                    i += 1
                    continue
                seq = m.group(0)
                if seq == "\x1b[H":
                    self.r = self.c = 0
                elif seq in ("\x1b[J", "\x1b[2J", "\x1b[3J"):
                    self.grid = [[" "] * self.cols for _ in range(self.rows)]
                    self.r = self.c = 0
                # ignore SGR color codes and other CSI
                i = m.end()
                continue
            if ch == "\r":
                self.c = 0
            elif ch == "\n":
                self.r += 1
                self.c = 0
            elif ch == "\b":
                self.c = max(0, self.c - 1)
            else:
                if self.c < self.cols:
                    self.grid[self.r][self.c] = ch
                    self.c += 1
                if self.c >= self.cols:
                    self.c = 0
                    self.r += 1
            if self.r >= self.rows:
                self.grid.pop(0)
                self.grid.append([" "] * self.cols)
                self.r = self.rows - 1
            i += 1

    def lines(self):
        return ["".join(row) for row in self.grid]


def replay(cast_path):
    data = json.loads(Path(cast_path).read_text())
    term = Term(data["rows"], data["cols"])
    snapshots = []  # (time_sec, lines)
    t = 0.0
    for delay, text in data["events"]:
        t += delay
        term.write(text)
        snapshots.append((t, term.lines()))
    return snapshots, t, data["cols"], data["rows"]


def render_video(cast_path, out_mp4, fps=30, frame_dir=None):
    snapshots, total, cols, rows = replay(cast_path)
    W, H = 1600, 900

    # fit terminal
    fsize = 24
    font = ImageFont.truetype(FONT, fsize)
    fb = ImageFont.truetype(FONTB, 26)
    # measure cell
    asc, desc = font.getmetrics()
    cell_w = font.getlength("M")
    cell_h = asc + desc
    term_w = cell_w * cols
    term_h = cell_h * rows
    # clamp to canvas with padding
    pad_x = 60
    pad_top = 150
    max_w = W - 2 * pad_x
    if term_w > max_w:
        scale = max_w / term_w
        fsize = max(12, int(fsize * scale * 0.92))
        font = ImageFont.truetype(FONT, fsize)
        asc, desc = font.getmetrics()
        cell_w = font.getlength("M")
        cell_h = asc + desc
        term_w = cell_w * cols
        term_h = cell_h * rows
    ox = (W - term_w) / 2
    oy = pad_top

    # title bar
    title_h = cell_h + 18
    tx0, ty0 = ox, oy - title_h
    tx1, ty1 = ox + term_w, oy + term_h

    frame_dir = Path(frame_dir) if frame_dir else Path(out_mp4).parent / "gate_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    si = 0
    n = int(total * fps) + 5
    for fno in range(n):
        t = fno / fps
        while si + 1 < len(snapshots) and snapshots[si + 1][0] <= t:
            si += 1
        lines = snapshots[si][1]
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        # faint pixel grid
        for x in range(0, W, 16):
            d.line([(x, 0), (x, H)], fill=(0, 26, 90), width=1)
        for y in range(0, H, 16):
            d.line([(0, y), (W, y)], fill=(0, 26, 90), width=1)
        # header caption
        d.text((ox, 60), "THE SPINE — CONTINUOUS UNEDITED SIBYL GATE",
               font=fb, fill=CYAN)
        d.text((ox, 100), "real stdout · real timing · separate processes · live UTC + code revision",
               font=ImageFont.truetype(FONT, 18), fill=GRAY)
        # title bar
        d.rounded_rectangle((tx0 - 4, ty0 - 4, tx1 + 4, ty1 + 4), radius=10,
                            outline=BLUE, fill=TERM_BG, width=2)
        d.rectangle((tx0, ty0, tx1, oy), fill=TITLEBG)
        d.text((tx0 + 14, ty0 + 8), "sibyl@hackathon: ~/dejavu", font=ImageFont.truetype(FONT, 18), fill=WHITE)
        d.text((tx1 - 110, ty0 + 8), f"{cols}×{rows}", font=ImageFont.truetype(FONT, 18), fill=GRAY)
        # terminal text
        y = oy
        for line in lines:
            d.text((ox + 6, y), line, font=font, fill=WHITE)
            y += cell_h
        # blinking block cursor
        if (fno // 15) % 2 == 0:
            # place at last non-space cursor region (approximate: end of content)
            d.rectangle((ox + 6 + term_w - cell_w, oy + (rows - 1) * cell_h,
                         ox + 6 + term_w, oy + rows * cell_h), fill=CYAN)
        # timestamp footer
        d.text((ox, oy + term_h + 30), f"t={t:05.2f}s  ·  unedited",
               font=ImageFont.truetype(FONT, 16), fill=DIM)
        img.save(frame_dir / f"f{fno:05d}.png")

    # assemble
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i",
           str(frame_dir / "f%05d.png"), "-c:v", "libx264", "-preset", "medium",
           "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:], file=sys.stderr)
        raise SystemExit(r.returncode)
    print(f"rendered {out_mp4} ({Path(out_mp4).stat().st_size} bytes, {total:.1f}s)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cast")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--frame-dir", default=None)
    a = ap.parse_args()
    render_video(a.cast, a.out, a.fps, a.frame_dir)
