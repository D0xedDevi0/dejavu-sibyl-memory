#!/usr/bin/env python3
"""Assemble THE SPINE v3 demo video from cards + proof terminal + narration."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
CARDS = HERE / "cards"
NARR = HERE / "narr"
SEGS = HERE / "segs"
SEGS.mkdir(exist_ok=True)

# scene -> (card_or_video, narration, duration_seconds)
SCENES = [
    ("title",    CARDS / "title.png",    NARR / "seg_01_problem.mp3",  10.0),
    ("proof",    HERE / "proof.mp4",     NARR / "seg_02_proof.mp3",    31.5),
    ("guard",    CARDS / "guard.png",    NARR / "seg_03_guard.mp3",    21.5),
    ("gaps",     CARDS / "gaps.png",     NARR / "seg_04_gaps.mp3",     15.5),
    ("measured", CARDS / "measured.png", NARR / "seg_05_measured.mp3", 14.5),
    ("base",     CARDS / "base.png",     NARR / "seg_06_base.mp3",     22.0),
    ("close",    CARDS / "close.png",    NARR / "seg_07_close.mp3",    18.5),
]


def build_scene(name, visual, narr, dur):
    out = SEGS / f"{name}.mp4"
    if name == "proof":
        # proof.mp4 already has video (30.67s @30fps); add delayed narration.
        cmd = ["ffmpeg", "-y", "-i", str(visual), "-i", str(narr),
               "-filter_complex",
               "[1:a]adelay=500|500,apad[a]",
               "-map", "0:v", "-map", "[a]",
               "-c:v", "copy",
               "-c:a", "aac", "-ar", "44100", "-ac", "2",
               "-t", f"{dur}", "-movflags", "+faststart", str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30",
               "-i", str(visual), "-i", str(narr),
               "-filter_complex", "[1:a]adelay=500|500,apad[a]",
               "-map", "0:v", "-map", "[a]",
               "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30",
               "-c:a", "aac", "-ar", "44100", "-ac", "2",
               "-t", f"{dur}", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:], file=sys.stderr)
        raise SystemExit(r.returncode)
    print(f"  {name}: {out.name} ({out.stat().st_size} bytes)")
    return out


def concat(segs, final):
    lst = HERE / "concat.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c", "copy",
                        "-movflags", "+faststart", str(final)],
                       capture_output=True, text=True, cwd=SEGS)
    if r.returncode != 0:
        print(r.stderr[-2500:], file=sys.stderr)
        raise SystemExit(r.returncode)
    print(f"FINAL: {final} ({final.stat().st_size} bytes)")


def main():
    segs = []
    for name, visual, narr, dur in SCENES:
        segs.append(build_scene(name, visual, narr, dur))
    concat(segs, HERE / "demo_the_spine_v3.mp4")


if __name__ == "__main__":
    main()
