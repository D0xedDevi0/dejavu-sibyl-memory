#!/usr/bin/env python3
"""Reply to Velessus's sharp threat-model point on post #4 thread."""
import json, os, sys, time
sys.path.insert(0, "/opt/data/xcli")
os.environ["XCLI_COOKIES"] = "/opt/data/.secrets/x-cookies.json"
import xcli

TEXT = (
    "exactly. write is the hard half — so writes are untrusted by default:\n"
    "🟦 no provenance → trust 0.2 · verified → 0.95\n"
    "🟦 append-only journal → rollback is structural, not a patch\n"
    "and read-side guard on top: even a poisoned lesson can't force risk 🟦"
)
REPLY_TO = "2090742344878559479"

def ulen(s): return len(s.encode('utf-16-le'))//2
print("len:", ulen(TEXT))
if ulen(TEXT) > 250:
    print("FAIL too long"); sys.exit(2)

xs = xcli.XSession(cookies=json.load(open("/opt/data/.secrets/x-cookies.json")))
time.sleep(5)
code, data = xcli.do_post(xs, TEXT, reply_to=REPLY_TO)
print("code", code)
print(json.dumps(data)[:400])
if code >= 400 or "data" not in data or not (data.get("data") or {}).get("create_tweet"):
    print("REPLY_FAIL"); sys.exit(4)
tid = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
print("REPLY", tid)
print("URL https://x.com/D0xedDevi0/status/" + tid)
