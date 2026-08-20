#!/usr/bin/env python3
"""Fill the NEURAL_MESH build page on hack.sibyllabs.org (headless Playwright).
Waits for React hydration, fills all fields, checks the honest memory
primitives, saves. Does NOT mark ready (that's the user's call / later).
"""
from playwright.sync_api import sync_playwright

TOKEN = "d103701110ba9d532e01ba0e3e403936a3272cbe80ebc499"
URL = f"https://hack.sibyllabs.org/team/enter?slug=neural-mesh-eea5&token={TOKEN}"
exe = "/opt/data/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"

REPO = "https://github.com/BasedNUKEM/NEURAL_MESH"
VIDEO = "https://x.com/D0xedDevi0/status/2090434125131907365"  # polished narrated demo (X post)
POSTS = ("https://x.com/D0xedDevi0/status/2089449978020421665\n"
         "https://x.com/D0xedDevi0/status/2089530925692379553\n"
         "https://x.com/D0xedDevi0/status/2090434125131907365")
DELETION = ("Without memory the agent forgets every past outcome: a cold-start session "
            "reverts to the naive book and stays overweight equity through the next crisis, "
            "taking the same ~-18% drawdown over and over. It becomes a stateless agent that "
            "can't learn, can't compound, and can't act on what it remembers.")
WALK = ("Persist: after a losing crisis the agent distills a lesson and writes it (WARM "
        "entity) plus the outcome to the COLD journal in its Sibyl SQLite store.\n"
        "Recall (fresh session): a cold-start process with zero chat history queries Sibyl "
        "FTS5, finds that lesson, and reallocates before deciding.\n"
        "Changes the decision by: flipping from naive (equity 0.55, -18%) to de-risk "
        "(equity 0.05, survives) — which then fires a real Base transaction. Wipe the store and it breaks.")
PRIMS = ["recall", "entities", "semantic search", "temporal / time-travel",
         "reflection", "consolidation"]   # honest: what dejavu actually uses

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, headless=True,
                          args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3000)  # hydration

    pg.fill('input[name="repoUrl"]', REPO)
    pg.fill('input[name="videoUrl"]', VIDEO)
    pg.fill('textarea[name="postUrls"]', POSTS)
    pg.fill('textarea[name="deletionImpact"]', DELETION)
    pg.fill('textarea[name="memoryWalkthrough"]', WALK)
    for prim in PRIMS:
        pg.eval_on_selector(f'input[name="memoryPrimitives"][value="{prim}"]',
            "el=>{el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true}))}")
    pg.click('form button[type="submit"]')
    pg.wait_for_timeout(6000)
    txt = pg.locator("body").inner_text()
    print("=== AFTER SAVE (tail) ===")
    print(txt[-1200:])
    b.close()
