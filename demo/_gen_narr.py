#!/usr/bin/env python3
"""Generate THE SPINE narration segments with the deep/confident D0xed voice.

Voice: edge-tts en-US-BrianNeural, rate -4%, pitch -4Hz.
Output: demo/narr/spine_segNN.mp3  (for the demo video).
"""
import asyncio, re, sys
from pathlib import Path
from edge_tts import Communicate

VOICE = "en-US-BrianNeural"
RATE = "-4%"
PITCH = "-4Hz"
HERE = Path(__file__).parent
OUT = HERE / "spine_narr"
OUT.mkdir(parents=True, exist_ok=True)

def parse_manifest():
    txt = (HERE / "narr" / "the_spine_narration.txt").read_text()
    segs = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # "01_open   text..."
        m = re.match(r"^([\w]+)\s+(.+)$", line)
        if m:
            segs.append((m.group(1), m.group(2).strip()))
    return segs

async def gen():
    segs = parse_manifest()
    for tag, text in segs:
        # normalize for TTS
        text = text.replace("THE SPINE", "The Spine").replace("THE FLEET", "The Fleet")
        text = text.replace("NEURAL_MESH", "Neural Mesh").replace("Sibyl", "Sibyl")
        text = text.replace("on-chain", "on chain").replace("x402", "x four oh two")
        c = Communicate(text=text, voice=VOICE, rate=RATE, pitch=PITCH)
        out = OUT / f"spine_{tag}.mp3"
        await c.save(str(out))
        print(f"  {tag}: {out.name}  ({out.stat().st_size} bytes)")
    print(f"done -> {OUT}")

if __name__ == "__main__":
    asyncio.run(gen())
