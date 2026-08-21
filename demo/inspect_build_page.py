#!/usr/bin/env python3
"""Inspect the Sibyl build page via the tokenized enter link."""
from playwright.sync_api import sync_playwright

URL = ("https://hack.sibyllabs.org/team/enter?slug=neural-mesh-eea5"
       "&token=PASTE_BUILD_TOKEN")
exe = "/opt/data/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, headless=True,
                          args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3500)
    print("URL:", pg.url)
    print("=== BODY TEXT ===")
    print(pg.locator("body").inner_text()[-3500:])
    print("=== INPUTS ===")
    inputs = pg.eval_on_selector_all("input, textarea, select",
        "els=>els.map(e=>({tag:e.tagName,type:e.type||'',name:e.name||'',value:e.value||'',checked:e.checked||false,ph:e.placeholder||''}))")
    for i in inputs: print(i)
    print("=== BUTTONS ===")
    btns = pg.eval_on_selector_all("button",
        "els=>els.map(e=>({txt:(e.innerText||'').trim().slice(0,50),type:e.type||'',disabled:e.disabled||false}))")
    for bt in btns: print(bt)
    b.close()
