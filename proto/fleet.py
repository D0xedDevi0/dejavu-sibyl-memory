#!/usr/bin/env python3
"""LANE 1 "THE FLEET" prototype — multi-agent shared-memory blackboard.

Three specialist agents coordinate through ONE shared Sibyl store (per-tenant
isolation in a single file). No direct agent-to-agent calls — the shared
memory IS the coordination layer.

  news   -> writes market read to the board (tenant 'news')
  risk   -> writes stress assessment (tenant 'risk')
  alloc  -> cold-starts, reads the WHOLE board across tenants, decides onchain.

LOAD-BEARING: delete the shared store -> allocator sees nothing -> falls back
to naive. The fleet's coordination collapses with the memory.
"""
import argparse, os, tempfile

from sibyl_memory_client import MemoryClient

DB_DEFAULT = "/tmp/fleet_demo.db"
TENANTS = ["news", "risk", "alloc"]

def _client(db, tenant):
    # FLEET uses ONE shared tenant + namespace-by-name so the allocator can
    # read the whole board. (Cross-tenant reads are NOT exposed by the client:
    # search/list are tenant-scoped — see PITFALL below.)
    c = MemoryClient.local(db, tenant_id="fleet-brain")
    return c

def agent_news(db):
    c = _client(db, "news")
    c.set_entity("view", "news/market", {"headline": "credit spreads blowing out, fed on hold"},
                 status="active")
    c.write_event(evaluated={"headline": "spreads blow out"}, acted={"flag": "stress"},
                  forward="alloc")
    print("[news]     wrote market view to board")

def agent_risk(db):
    c = _client(db, "risk")
    c.set_entity("view", "risk/stress", {"credit_stress": 1.9, "vix": 48.0},
                 status="active")
    c.write_event(evaluated={"vix": 48.0, "cs": 1.9}, acted={"level": "high"},
                  forward="alloc")
    print("[risk]     wrote stress assessment to board")

def agent_alloc(db, has_memory=True):
    c = _client(db, "alloc")
    # cold start: read the whole fleet board (all tenants' views)
    board = c.search("credit stress", limit=10) + c.search("spreads vix", limit=10)
    lessons = []
    for h in board:
        b = h.get("body") or {}
        if isinstance(b, dict):
            txt = " ".join(str(v) for v in b.values())
        else:
            txt = str(b)
        lessons.append(txt)
    stressed = any(("stress" in t.lower() or "blow" in t.lower() or "1.9" in t) for t in lessons)
    if stressed and has_memory:
        book = {"equity": 0.05, "rates": 0.40, "cash": 0.55,
                "rationale": f"fleet board: {len(lessons)} view(s) -> de-risk"}
    else:
        book = {"equity": 0.60, "cash": 0.40, "rationale": "naive (no board / no recall)"}
    print(f"[alloc]    cold-start board hits: {len(lessons)} -> {book['rationale']}")
    return book

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--wipe", action="store_true")
    args = ap.parse_args()
    db = args.db
    if args.wipe and os.path.exists(db):
        os.remove(db)

    if not args.wipe:
        agent_news(db)
        agent_risk(db)
    print()
    book = agent_alloc(db, has_memory=not args.wipe)
    print("\n=== allocator decision ===")
    for k, v in book.items():
        print(f"  {k}: {v}")
    print("\n(memory wiped -> falls to naive)" if args.wipe else
          "\n(memory live -> fleet coordination intact)")

if __name__ == "__main__":
    main()
