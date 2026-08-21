#!/usr/bin/env python3
"""Post #4 — the safety/trust angle — via xcli as a 5-node thread.
Hook -> poison test -> why it's safe -> measured -> close+tags.
Designed to be retried by cron until daily write quota resets (err344).
Returns exit 0 only on full success.
"""
import json, os, sys, time
sys.path.insert(0, "/opt/data/xcli")
os.environ["XCLI_COOKIES"] = "/opt/data/.secrets/x-cookies.json"
import xcli

NODES = [
    "the hot take on agent memory isn't recall.\nit's TRUST. 🧠🛡️\n\n"
    "everyone builds memory that remembers MORE.\n"
    "nobody builds memory that can't be WEAPONIZED.\n\n"
    "so we shipped the guard — for @sibylcap, on @base. 👇",

    "🟦 THE POISON TEST — we hacked our own agent's memory.\n\n"
    "we wrote a *compromised* lesson telling it to:\n"
    "→ max long equity in a crisis\n\n"
    "the agent ignored it.\n"
    "took ZERO extra risk. stayed safe. 🟦",

    "🟦 WHY — memory informs. it doesn't override.\n\n"
    "the risk framework owns the allocation, not free-text prose.\n"
    "a poisoned memory can't force a bad decision.\n\n"
    "🟦 selective forgetting works:\n"
    "delete one bad lesson → the rest survive → decision stays right.",

    "🟦 MEASURED, NOT MARKETED\n"
    "→ compromised lesson: no risk (reproducible failure-mode guard)\n"
    "→ 200 frames: +7.07pp averted · 75% flip\n"
    "→ 12 crises: $0.90 vs $0.29\n\n"
    "🟦 and it ACTS: recalled lesson → real @base tx.\n"
    "memory-driven, safety-guarded, onchain.",

    "🟦 memory you can TRUST is the only memory that scales.\n\n"
    "that's dejavu. MIT. built in the open.\n"
    "github.com/BasedNUKEM/NEURAL_MESH\n\n"
    "@base @sibylcap @virtuals_io\n"
    "forgetting is a bug. remembering is the strategy. 🤖",
]

def ulen(s): return len(s.encode('utf-16-le'))//2
for i, n in enumerate(NODES):
    u = ulen(n)
    print(f"node{i}: {u} units")
    if u > 250:
        print(f"FAIL node{i} {u} > 250"); sys.exit(2)

xs = xcli.XSession(cookies=json.load(open("/opt/data/.secrets/x-cookies.json")))
code, data = xcli.do_post(xs, NODES[0])
if code >= 400 or "data" not in data or not (data.get("data") or {}).get("create_tweet"):
    print("MAIN_FAIL", code, json.dumps(data)[:400]); sys.exit(4)
main_id = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
print("MAIN", main_id)

prev = main_id
for i, node in enumerate(NODES[1:], start=1):
    code, data = xcli.do_post(xs, node, reply_to=prev)
    if code >= 400 or not (data.get("data") or {}).get("create_tweet"):
        print(f"REPLY{i}_FAIL", code, json.dumps(data)[:300]); sys.exit(5)
    prev = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
    print(f"REPLY{i}", prev)
    time.sleep(1.5)

print("THREAD_DONE", main_id)
print("URL https://x.com/D0xedDevi0/status/" + main_id)
