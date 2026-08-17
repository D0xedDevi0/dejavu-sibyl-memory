#!/usr/bin/env python3
"""NEURAL_MESH x Sibyl Memory — memory-echo loop prototype.

Demonstrates the LOAD-BEARING pattern for the Sibyl Memory Hackathon:

  1. SESSION A: agent reads a market frame, makes a decision, records the
     outcome + a distilled LESSON into Sibyl Memory (WARM entity + COLD journal).
  2. Close / fresh process (cold start, no conversation state).
  3. SESSION B: agent cold-starts with ZERO context, queries Sibyl Memory,
     recalls the lesson, and DECIDES DIFFERENTLY than a memory-less agent.

If you delete the Sibyl store (the `--wipe` flag), the agent reverts to a
naive policy and makes the losing call -> core function breaks. That is the
deletion test that makes memory load-bearing.

Runtime: pure local SQLite via MemoryClient.local(). No account, no network.
"""
import argparse, json, os, sys, tempfile

from sibyl_memory_client import MemoryClient

# ---- naive policy (memory-less baseline) -------------------------------
def naive_decision(frame: dict) -> dict:
    """A book that ignores history entirely. In a crisis it stays long equity."""
    return {"equity": 0.55, "credit": 0.20, "rates": 0.10, "cash": 0.15,
            "rationale": "naive: overweight equity, no recall of past losses"}

# ---- memory-driven policy ----------------------------------------------
def memory_decision(frame: dict, client: MemoryClient) -> dict:
    """Recall lessons from Sibyl Memory and let them change the book."""
    # recall: search for past crisis lessons
    hits = client.search("credit stress crisis lesson", limit=5)
    hits += client.search("drawdown loss recovery", limit=5)
    crisis_lessons = []
    for h in hits:
        body = h.get("body") or {}
        # bodies may be dicts with a 'lesson' or plain text
        if isinstance(body, dict):
            if body.get("lesson"):
                crisis_lessons.append(body["lesson"])
        elif isinstance(body, str):
            crisis_lessons.append(body)
        elif isinstance(body, list):
            crisis_lessons.append(json.dumps(body))

    cs = frame.get("credit_stress", 0.0)
    vix = frame.get("vix", 0.0)
    stressed = cs > 0.7 or vix > 30

    if stressed and crisis_lessons:
        # memory says: de-risk in stress
        return {"equity": 0.05, "credit": 0.03, "rates": 0.40, "hedges": 0.20,
                "cash": 0.32,
                "rationale": f"recalled {len(crisis_lessons)} crisis lesson(s) "
                             f"-> de-risked into cash/rates"}
    return naive_decision(frame)

# ---- session A: learn & persist ----------------------------------------
def session_a(client: MemoryClient, frame: dict):
    outcome = {"equity_return": -0.18, "credit_return": -0.22,
               "max_drawdown": -0.24}
    lesson = ("When credit_stress > 0.7 or vix > 30, staying overweight equity "
              "produces -18%+ drawdown. De-risk to cash/rates instead.")
    # WARM entity (single source of truth, category='lesson')
    client.set_entity("lesson", "crisis-derisking",
                      {"lesson": lesson, "frame": frame, "outcome": outcome},
                      status="active")
    # COLD journal entry (append-only audit)
    client.write_event(evaluated={"vix": frame["vix"], "cs": frame["credit_stress"]},
                       acted={"equity": 0.55, "credit": 0.20},
                       forward="NA", extra={"drawdown": -0.24, "lesson_id": "crisis-derisking"})
    print("[SESSION A] wrote lesson 'crisis-derisking' + journal event")

# ---- session B: cold start & recall ------------------------------------
def session_b(client: MemoryClient, frame: dict) -> dict:
    # cold start: no conversation history. Query memory.
    return memory_decision(frame, client)

# ---- main --------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="path to memory.db (default: temp)")
    ap.add_argument("--wipe", action="store_true", help="delete the store first (simulate no memory)")
    ap.add_argument("--crisis", action="store_true", help="use a crisis frame")
    args = ap.parse_args()

    db = args.db or os.path.join(tempfile.mkdtemp(), "memory.db")
    if args.wipe and os.path.exists(db):
        os.remove(db)

    # the load-bearing moments: set_entity / get_entity / search
    client = MemoryClient.local(db)

    if not args.wipe:
        session_a(client, {} if not args.crisis else
                  {"vix": 48.0, "credit_stress": 1.9})

    # fresh cold-start process would reopen the DB here
    client2 = MemoryClient.local(db)

    crisis_frame = {"vix": 52.0, "credit_stress": 2.2} if args.crisis else \
                   {"vix": 18.0, "credit_stress": 0.3}

    d = session_b(client2, crisis_frame)
    print(f"[SESSION B] frame vix={crisis_frame['vix']} cs={crisis_frame['credit_stress']}")
    print(f"[SESSION B] decision: {json.dumps(d, indent=2)}")
    print(f"[SESSION B] equity weight = {d['equity']:.2f}  (memory-loaded)"
          if not args.wipe else
          f"[SESSION B] equity weight = {d['equity']:.2f}  (NAIVE - memory wiped)")
    print(f"[SESSION B] stored DB: {db}")

if __name__ == "__main__":
    main()
