#!/usr/bin/env bash
# Silent retry watchdog: post the dejavu demo reply to the drop thread.
# Prints the tweet URL ONLY on success (fire-and-forget watchdog pattern).
# While quota-blocked, stays silent so the cron tick reports nothing.
export HOME=/opt/data
export XCLI_COOKIES=/opt/data/.secrets/x-cookies.json
cd /opt/data/sibyl-hackathon/demo

OUT=$(/opt/data/xcli-venv/bin/python fire_reply_demo.py 2>&1)
RC=$?
# Only surface on success (URL line) or a real non-quota error.
if echo "$OUT" | grep -q "URL https://"; then
  echo "🟦 dejavu demo reply posted: $(echo "$OUT" | grep 'URL https://' | sed 's/URL //')"
  exit 0
fi
# quota (344) or quota-variant -> stay silent, keep retrying later
if echo "$OUT" | grep -qE "344|daily limit|quota"; then
  exit 0
fi
# anything else that's a hard error -> report
if [ "$RC" -ne 0 ]; then
  echo "⚠️ dejavu demo reply: unexpected error ($RC). Tail:"
  echo "$OUT" | tail -5
  exit "$RC"
fi
exit 0
