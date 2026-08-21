#!/usr/bin/env python3
"""Re-open the build page to confirm the save persisted (values + milestones)."""
from playwright.sync_api import sync_playwright

TOKEN = "PASTE_BUILD_TOKEN"
URL = f"https://hack.sibyllabs.org/team/enter?slug=neural-mesh-eea5&token={TOKEN}"
exe = "/opt/data/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, headless=True,
                          args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(3000)
    print("=== FIELD VALUES ===")
    vals = pg.eval_on_selector_all("input[name], textarea[name]",
        "els=>els.map(e=>({name:e.name,value:e.value||'',checked:e.checked||false}))")
    for v in vals: print(v)
    print("=== BODY (milestone circles) ===")
    t = pg.locator("body").inner_text()
    import re
    # find the milestone section
    idx = t.find("Public repo")
    print(t[idx:idx+220])
    b.close()
