#!/usr/bin/env python3
"""Generate only the NEW THE SPINE narration segments (11_loop, 12_conflict,
13_earns, 14_close) with the deep/confident D0xed voice, matching manifest text."""
import asyncio, re
from pathlib import Path
from edge_tts import Communicate

VOICE = "en-US-BrianNeural"
RATE = "-4%"
PITCH = "-4Hz"
HERE = Path(__file__).parent
OUT = HERE / "spine_narr"
OUT.mkdir(parents=True, exist_ok=True)

# New/changed segments: (tag, manifest text verbatim)
SEGS = [
    ("11_loop", "And now it remembers its own anchor. The on-chain mint receipt is written back into the store, so a fresh box proves it was committed on Base. The memory knows it owns itself."),
    ("12_conflict", "And it never overwrites the past. When a new belief contradicts an old one, the loser is archived, not destroyed. A full revision trail survives. Write-time conflict resolution."),
    ("13_earns", "And it earns. Real parties have already paid real USDC to read this memory, settled on chain, on Base. The memory is not a database. It is an economy."),
    ("14_close", "Forgetting is a bug. Remembering is the strategy. THE SPINE. NEURAL MESH, times, Sibyl Memory."),
]

async def gen():
    for tag, text in SEGS:
        c = Communicate(text=text, voice=VOICE, rate=RATE, pitch=PITCH)
        out = OUT / f"spine_{tag}.mp3"
        await c.save(str(out))
        print(f"  {tag}: {out.name} ({out.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(gen())
    print(f"done -> {OUT}")
