#!/usr/bin/env python3
"""Generate v3 narration mp3s from narration.json (edge-tts, BrianNeural)."""
import asyncio, json
from pathlib import Path
from edge_tts import Communicate

VOICE = "en-US-BrianNeural"
RATE = "-4%"
PITCH = "-4Hz"
HERE = Path(__file__).parent
MANIFEST = HERE / "narration.json"
OUT = HERE / "narr"
OUT.mkdir(parents=True, exist_ok=True)

async def gen():
    segs = json.loads(MANIFEST.read_text())
    for s in segs:
        c = Communicate(text=s["text"], voice=VOICE, rate=RATE, pitch=PITCH)
        out = OUT / f"seg_{s['tag']}.mp3"
        await c.save(str(out))
        print(f"  {s['tag']}: {out.name} ({out.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(gen())
    print(f"done -> {OUT}")
