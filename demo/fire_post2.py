#!/usr/bin/env python3
"""Post the dejavu demo thread (post #2) via xcli. Fires main + 4 replies.
Designed to be retried by cron until the account's daily write quota resets.
Main node carries the demo video. Returns exit 0 only on full success.
"""
import json, os, sys, time
sys.path.insert(0, "/opt/data/xcli")
os.environ["XCLI_COOKIES"] = "/opt/data/.secrets/x-cookies.json"
import xcli

NODES = [
    "dejavu. I've seen this crisis before — so I de-risk. 🧠💙\n\nAn agent whose onchain (@base) decisions are driven by its own memory.\nBuilt for the @sibylcap hackathon.\n\n🟦 It lost. It remembered. It survived. 🎥👇",
    "🟦 THE GATE — same vix=52 crisis, only memory differs:\n🟢 memory-loaded → de-risk → equity 0.05 · real @base tx\n🔴 memory wiped → naive → equity 0.55 · −18%\n\nDelete the store, the core function breaks. Load-bearing memory, not a decorated logger.",
    "🟦 MEASURED — 200 frames · seed 1337\n🟢 with memory: −2.83% mean\n🔴 no memory: −9.90%\n→ +7.07pp averted · 75% decisions changed\n12 crises: $0.90 vs $0.29. Remembering compounds.",
    "🟦 THE BRAIN — runs on NEURAL_MESH, six agentic-memory lanes:\nA provenance · B forgetting · C pay-to-remember (x402)\nD memory→LoRA · E prospective · F token-budget\nStack: @base + @virtuals (ACP agent). One story, two engines.",
    "🟦 BUILD-IN-PUBLIC\nRepo: github.com/BasedNUKEM/NEURAL_MESH (MIT)\nLive brain: api.d0xeddev.com/brain\nSibyl Memory hackathon · @sibylcap\nForgetting is a bug. Remembering is the strategy. 🤖",
]
VIDEO = "/opt/data/sibyl-hackathon/demo/demo_video.mp4"
QUOTA = "344"

def ulen(s): return len(s.encode('utf-16-le'))//2
for i, n in enumerate(NODES):
    if ulen(n) > 250:
        print(f"FAIL node{i} {ulen(n)} units > 250"); sys.exit(2)

xs = xcli.XSession(cookies=json.load(open("/opt/data/.secrets/x-cookies.json")))

# main node with video
try:
    m = xcli.media_upload(xs, VIDEO)
except Exception as e:
    print("MEDIA_ERR", e); sys.exit(3)
code, data = xcli.do_post(xs, NODES[0], media_ids=[m])
if code >= 400 or "data" not in data or not (data.get("data") or {}).get("create_tweet"):
    print("MAIN_FAIL", code, json.dumps(data)[:300])
    sys.exit(4)
main_id = (data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"])
print("MAIN", main_id)

# replies
prev = main_id
for i, node in enumerate(NODES[1:], start=1):
    code, data = xcli.do_post(xs, node, reply_to=prev)
    if code >= 400 or not (data.get("data") or {}).get("create_tweet"):
        print(f"REPLY{i}_FAIL", code, json.dumps(data)[:200])
        sys.exit(5)
    prev = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
    print(f"REPLY{i}", prev)
    time.sleep(1.5)

print("THREAD_DONE", main_id)
