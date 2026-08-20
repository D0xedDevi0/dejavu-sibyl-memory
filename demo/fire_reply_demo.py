#!/usr/bin/env python3
"""Reply to the dejavu demo thread with the polished narrated video.
Tags @sibylcap + @base + @virtuals_io. Returns 0 only on success.
"""
import json, os, sys
sys.path.insert(0, "/opt/data/xcli")
os.environ["XCLI_COOKIES"] = "/opt/data/.secrets/x-cookies.json"
import xcli

TEXT = ("Polished demo is live 🎥🧠💙\n\n"
        "🟦 Forgetting is a bug. Remembering is the strategy.\n"
        "🟦 It lost. It remembered. It survived — on a real @base tx.\n"
        "🟦 Wipe the store → it breaks.\n\n"
        "For the @sibylcap hackathon. @base + @virtuals_io. 🟦🚀")
REPLY_TO = "2089530925692379553"   # the dejavu drop thread
VIDEO = "/opt/data/sibyl-hackathon/demo/demo_video_v2.mp4"

def ulen(s): return len(s.encode('utf-16-le'))//2
print("length units:", ulen(TEXT))
if ulen(TEXT) > 250:
    print("FAIL too long"); sys.exit(2)

xs = xcli.XSession(cookies=json.load(open("/opt/data/.secrets/x-cookies.json")))
try:
    m = xcli.media_upload(xs, VIDEO)
except Exception as e:
    print("MEDIA_ERR", e); sys.exit(3)
code, data = xcli.do_post(xs, TEXT, media_ids=[m], reply_to=REPLY_TO)
print("code", code)
print(json.dumps(data)[:400])
if code >= 400 or "data" not in data or not (data.get("data") or {}).get("create_tweet"):
    print("POST_FAIL"); sys.exit(4)
tid = data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
print("REPLY_ID", tid)
print("URL https://x.com/D0xedDevi0/status/" + tid)
