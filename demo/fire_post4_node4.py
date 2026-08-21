#!/usr/bin/env python3
"""Fire the missing node 4 (close+tags) as a reply to node 3 of post #4 thread."""
import json, os, sys, time
sys.path.insert(0, "/opt/data/xcli")
os.environ["XCLI_COOKIES"] = "/opt/data/.secrets/x-cookies.json"
import xcli

NODE4 = (
    "🟦 memory you can TRUST is the only memory that scales.\n\n"
    "that's dejavu. MIT. built in the open.\n"
    "github.com/BasedNUKEM/NEURAL_MESH\n\n"
    "@base @sibylcap @virtuals_io\n"
    "forgetting is a bug. remembering is the strategy. 🤖"
)
REPLY_TO = "2090738152482934992"  # node 3 id

def ulen(s): return len(s.encode('utf-16-le'))//2
print("len:", ulen(NODE4))
if ulen(NODE4) > 250: sys.exit(2)

xs = xcli.XSession(cookies=json.load(open("/opt/data/.secrets/x-cookies.json")))
time.sleep(8)  # space out from the burst that tripped the rate guard
code, data = xcli.do_post(xs, NODE4, reply_to=REPLY_TO)
print("code", code)
print(json.dumps(data)[:400])
if code >= 400 or "data" not in data or not (data.get("data") or {}).get("create_tweet"):
    print("REPLY4_FAIL"); sys.exit(4)
tid = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
print("REPLY4", tid)
print("URL https://x.com/D0xedDevi0/status/" + tid)
