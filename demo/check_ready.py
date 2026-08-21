#!/usr/bin/env python3
"""Check the 'Mark ready for judging' toggle state on the build page."""
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
    t = pg.locator("body").inner_text()
    idx = t.find("Ready for judging")
    print("=== READY SECTION ===")
    print(t[idx:idx+200])
    # look for any aria-checked / checkbox state in the ready toggle
    chk = pg.eval_on_selector_all("input[type=checkbox], [role=checkbox], button",
        "els=>els.map(e=>({txt:(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,40),aria:e.getAttribute('aria-checked'),cls:(e.className||'').slice(0,60)}))")
    print("=== TOGGLE CANDIDATES ===")
    for c in chk:
        if 'ready' in (c['txt']+c['cls']).lower() or c['aria'] is not None:
            print(c)
    b.close()
