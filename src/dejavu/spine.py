"""THE SPINE — the fused five-layer Sovereign Memory system, run as one story.

This is the upgraded headline for the hackathon: not five features, one spine.

    The agent doesn't *have* memory. The memory IS the agent — and it owns
    itself, earns from itself, and writes itself.

Five layers, one system:
    L1 Sovereign   — memory root is committed onchain (ownable asset).    [sovereign.py]
    L2 Identity    — the agent IS its memory (portable across boxes).     [sovereign.py]
    L3 Dream       — memory authors new skills while idle (Learner/DREAM).[memory.py]
    L4 Commons     — many agents coordinate through one shared pool.      [fleet.py]
    L5 Regret      — memory of the road not taken.                        [regret.py]
    L6 Temporal    — memory knows WHEN + strategic forgetting to ARCH.    [temporal.py]

`run_arc()` executes the whole thing as one continuous demo arc (session A learns
-> counterfactual -> sovereign mint -> fresh box same being -> dream a skill ->
wipe -> asset orphaned + naive). `dejavu-sovereign` CLI wraps it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .config import Config
from .memory import Memory
from .policy import de_risk_book, naive_book
from .regret import regret_urgency, write_regret
from .sovereign import (asset_orphaned, identity, is_same_being, ledger_balance,
                        memory_root, record_payment, sovereign_mint)

# Default store lives in the repo data/ dir.
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "sovereign.db"
CRISIS_FRAME = {"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0,
                "yield_slope": 0.6}


def _w(s: str) -> None:
    print(s, flush=True)


def run_arc(db: str | Path = DEFAULT_DB, *, dry_run: bool = True) -> dict:
    """Run the full five-layer arc and return a dict of every stage's proof."""
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config(db_path=db, dry_run=dry_run)
    out: dict[str, object] = {}

    # ---- L5 + L1 + L2: session A learns a lesson AND a regret ------------
    mem = Memory(str(db), tenant_id="sovereign-brain")
    mem.delete_store()
    mem = Memory(str(db), tenant_id="sovereign-brain")
    mem.write_lesson("crisis-1", "de-risk to <=5% equity when credit stress spikes",
                     frame=CRISIS_FRAME, outcome={"averted": 18.0})
    write_regret(mem, "crisis-1", taken="de-risked to cash",
                 road_not_taken="stayed overweight equity", would_have_lost=18.0)
    out["lessons_written"] = mem.list_lessons()  # sanity

    # root BEFORE any onchain step (the committed fingerprint)
    root = memory_root(mem)
    out["root_before"] = root["root"]

    # ---- L1: sovereign mint (commit the root; dry-run by default) --------
    mint = sovereign_mint(mem, cfg)
    out["mint"] = mint.as_dict()
    out["asset_not_orphaned"] = not asset_orphaned(mem, mint)  # resolves now

    # ---- L4: shared-pool coordination echoes (news/risk -> alloc) --------
    mem.set_entity("view", "news/market", {"headline": "spreads blow out",
                                           "sentiment": "risk-off"}, status="active")
    mem.set_entity("view", "risk/stress", {"credit_stress": 2.2,
                                           "flags": ["spread_widening"]}, status="active")
    out["board_views"] = len(mem.list_entities(category="view"))

    # ---- L3: dream — seed the journal, then Learner proposes a skill ----
    # The Learner needs >= min_pattern_hits (3) journal patterns to propose, so
    # write a handful of recurring crisis events (the compounding evidence the
    # store authors NEW skills from).
    for i in range(4):
        mem.write_event(
            evaluated={"vix": 52.0, "credit_stress": 2.2, "cycle": i},
            acted={"book": "de-risk", "equity": 0.05},
            forward=f"alloc-{i}",
            extra={"outcome": "averted drawdown", "lesson": "de-risk on stress"},
        )
    try:
        learn = mem.learn()
        out["learn_created"] = learn["created"]
        props = mem.list_proposals(status="pending", limit=10)
        out["proposals"] = [p.id for p in props][:5]
        if props:
            accepted = mem.accept_proposal(props[0].id, note="spine arc")
            out["accepted_skill"] = accepted.get("doc_key")
            out["accepted"] = accepted.get("accepted")
    except Exception as e:  # pragma: no cover
        out["learn_error"] = str(e)

    # ---- L4: query economics — the store earns ---------------------------
    ledger = record_payment(mem, "view", "news/market", price_wei=1_000_000_000)
    out["query_ledger"] = ledger

    # ---- L2: capture identity at the FINAL content, then mount a fresh box
    # on the SAME store -> same being. (Compare identical content, not two
    # points in time — content is the identity.) ----------------------------
    ident_a = identity(mem)
    out["identity_a"] = ident_a["id"]
    mem2 = Memory(str(db), tenant_id="sovereign-brain")
    ident_b = identity(mem2)
    out["identity_b"] = ident_b["id"]
    out["same_being"] = is_same_being(ident_a, ident_b)
    out["regret_urgency"] = regret_urgency(mem2, ["road not taken would have lost"])
    mem2.close()

    # ---- L6: temporal memory + strategic forgetting (the dynamic layer) ---
    # The agent remembers WHEN it knew things, forgets stale lessons ON PURPOSE
    # (to ARCH, recoverable), and keeps the live store lean. This is deliberate,
    # auditable forgetting — NOT the wipe (which is destructive).
    from .temporal import consolidate, reconstruct_past, touch_lesson
    try:
        touch_lesson(mem, "crisis-1", note="reinforced in this arc")
        consol = consolidate(mem, max_age_days=7)  # crisis-1 is fresh -> retained
        out["consolidated"] = consol["archived"]
        out["consolidation_retained"] = consol["retained"]
        out["archive_recoverable"] = len(reconstruct_past(mem))
    except Exception as e:  # pragma: no cover
        out["consolidation_error"] = str(e)

    # ---- policy: with memory it de-risks ---------------------------------
    lessons = mem.recall_lessons(["credit stress crisis lesson"])
    book_with = de_risk_book(len(lessons), risk=1.0)
    out["book_with_memory_equity"] = round(book_with.equity, 3)

    # ---- the wipe: delete the store --------------------------------------
    mem.delete_store()
    mem = Memory(str(db), tenant_id="sovereign-brain")
    out["asset_orphaned_after_wipe"] = asset_orphaned(mem, mint)  # True
    out["identity_after_wipe"] = identity(mem)["id"]
    out["same_being_after_wipe"] = is_same_being(ident_a, identity(mem))  # False
    out["book_without_memory_equity"] = round(naive_book().equity, 3)
    out["ledger_after_wipe"] = ledger_balance(mem)  # the earnings are gone too
    mem.close()

    out["dry_run"] = dry_run
    return out


def _fmt(out: dict) -> str:
    L = []
    L.append("🟦 THE SPINE — memory as an ownable, self-authoring data layer")
    L.append(f"   root: {out['root_before']}")
    L.append(f"   L1 mint: {out['mint']['action'] if 'action' in out['mint'] else 'committed'} "
             f"root={out['mint']['root'][:16]}… dry_run={out['mint']['dry_run']}")
    L.append(f"   asset resolves: {out['asset_not_orphaned']}")
    L.append(f"   L2 identity A={out['identity_a']} B={out['identity_b']} "
             f"same_being={out['same_being']}")
    L.append(f"   L3 dreams: {len(out.get('proposals', []))} proposals -> "
             f"accepted={out.get('accepted_skill','-')}")
    L.append(f"   L4 query ledger: {out['query_ledger']['earned_wei']} wei from "
             f"{out['query_ledger']['paid_queries']} paid queries")
    L.append(f"   L5 regret urgency: {out['regret_urgency']}")
    L.append(f"   L6 consolidate: {out.get('consolidated', [])} archived, "
             f"{out.get('consolidation_retained', 0)} retained (fresh stays, "
             f"stale->ARCH, recoverable={out.get('archive_recoverable', 0)})")
    L.append(f"   WITH memory -> equity {out['book_with_memory_equity']} (de-risk)")
    L.append("   >>> DELETE STORE <<<")
    L.append(f"   asset orphaned: {out['asset_orphaned_after_wipe']}")
    L.append(f"   same_being: {out['same_being_after_wipe']} (new identity)")
    L.append(f"   WITHOUT memory -> equity {out['book_without_memory_equity']} (naive)")
    L.append(f"   query ledger wiped: {out['ledger_after_wipe']['earned_wei']} wei")
    L.append(f"   dry_run: {out['dry_run']}")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    dry_run = not (os.environ.get("DEJAVU_DRY_RUN", "1") == "0")
    if "--no-dry-run" in argv:
        dry_run = False
    db = DEFAULT_DB
    for i, a in enumerate(argv):
        if a == "--db" and i + 1 < len(argv):
            db = Path(argv[i + 1])
    out = run_arc(db, dry_run=dry_run)
    print(_fmt(out))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
