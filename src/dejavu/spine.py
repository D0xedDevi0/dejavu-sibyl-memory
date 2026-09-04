"""THE SPINE — the fused six-layer Sovereign Memory system, run as one story.

This is the upgraded headline for the hackathon: not six features, one spine.

    The agent doesn't *have* memory. The memory IS the agent — and it owns
    itself, earns from itself, and writes itself.

Six layers, one system (now eight beats):
    L1 Sovereign   — memory root is committed onchain (ownable asset).    [sovereign.py]
    L2 Identity    — the agent IS its memory (portable across boxes).     [sovereign.py]
    L3 Dream       — memory authors new skills while idle (Learner/DREAM).[memory.py]
    L4 Commons     — many agents coordinate through one shared pool.      [fleet.py]
    L5 Regret      — memory of the road not taken.                        [regret.py]
    L6 Temporal    — memory knows WHEN + strategic forgetting to ARCH.    [temporal.py]
    L7 Sovereign Loop — memory that knows it OWNS ITSELF: it records its own
                        onchain anchor back into the store (REFERENCE tier). [sovereign.py]
    L8 Conflict    — write-time conflict resolution (supersession): contradictions
                        are superseded to ARCH + journaled, not overwritten.  [supersede.py]

Then THE SECOND ACT (L9-L16) runs live on the same store before the wipe —
memory's relationship with ITSELF and with OTHER agents:
    L9 Discernment  — gate what gets written.          [gates.py]
    L10 Meta        — know what you don't know.        [meta.py]
    L11 Guard       — memory that says NO.             [guard.py]
    L12 Exchange    — memory that travels (verified).  [exchange.py]
    L13 Consensus   — agents agree on the truth.       [consensus.py]
    L14 Curriculum  — memory schedules its own learning.[curriculum.py]
    L15 Distill     — scar tissue becomes capability.  [distill.py]
    L16 Consent     — memory argues for its own life (the wipe becomes an
                      audited, negotiated act).        [consent.py]

`run_arc()` executes the whole thing as one continuous demo arc (session A learns
-> counterfactual -> sovereign mint + self-anchor -> fresh box same being -> dream
a skill -> supersede a conflict -> the full second act -> wipe -> asset orphaned +
naive). `dejavu-sovereign` CLI wraps it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .config import Config
from .memory import Memory
from .policy import de_risk_book, naive_book
from .regret import regret_urgency, write_regret
from .sovereign import (anchor_self, asset_orphaned, identity, is_same_being,
                        is_self_anchored, ledger_balance, memory_root,
                        record_payment, resolve_anchor, sovereign_mint)

# Default store lives in the repo data/ dir.
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "sovereign.db"
CRISIS_FRAME = {"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0,
                "yield_slope": 0.6}


def _w(s: str) -> None:
    print(s, flush=True)


def run_arc(db: str | Path = DEFAULT_DB, *, dry_run: bool = True) -> dict:
    """Run the full six-layer arc and return a dict of every stage's proof."""
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

    # ---- L7: self-referential sovereign loop — the memory anchors ITSELF.
    # The mint receipt is written back INTO the store (REFERENCE tier), so the
    # memory knows it owns this committed root. A fresh box mounting the same
    # store recalls its own onchain anchor as part of its content. --------
    anchor_self(mem, mint)
    out["self_anchored"] = is_self_anchored(mem, mint)
    out["anchor_resolves"] = (resolve_anchor(mem) or {}).get("root") == mint.root

    # ---- L4: shared-pool coordination echoes (news/risk -> alloc) --------
    mem.set_entity("view", "news/market", {"headline": "spreads blow out",
                                           "sentiment": "risk-off"}, status="active")
    mem.set_entity("view", "risk/stress", {"credit_stress": 2.2,
                                           "flags": ["spread_widening"]}, status="active")
    out["board_views"] = len(mem.list_entities(category="view"))

    # ---- L8: write-time conflict resolution — a contradiction is superseded,
    # not blindly overwritten. The old view is archived (recoverable) and a
    # SUPERSEDES journal event links old -> new. The memory resolves conflicts
    # on write, keeping an auditable revision trail. -------------------------
    from .supersede import supersede_entity, supersession_chain
    try:
        sup = supersede_entity(mem, "view", "risk/stress",
                               {"credit_stress": 3.1, "flags": ["full_crisis"]},
                               reason="stress escalated")
        out["superseded_prior"] = sup["superseded"] is not None
        out["supersession_chain_len"] = len(
            supersession_chain(mem, "view", "risk/stress"))
    except Exception as e:  # pragma: no cover
        out["supersession_error"] = str(e)

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

    # ==== THE SECOND ACT (L9-L16): what the field hasn't built ==============
    # Memory's relationship with itself and with other agents — run live on the
    # populated store, each beat deterministic and load-bearing.
    # Seed the crisis lesson with hard provenance so L11/L12/L15 can use it.
    from .meta import record_provenance
    record_provenance(mem, "lesson", "crisis-1", source="backtest",
                      evidence=3, falsifiable=True, hard=True)

    # -- L9 DISCERNMENT: noise refused, rich lesson gated in ---------------
    from .gates import gate_write
    noise_dec = gate_write(mem, "fact", "noise-1", {"note": "meh"})
    rich_dec = gate_write(mem, "lesson", "gated-rich",
                          {"lesson": "de-risk first, ask later when vix>30"},
                          source="arc", evidence=2, falsifiable=True)
    out["l9_noise_rejected"] = (noise_dec.action == "REJECT")
    out["l9_rich_persisted"] = (rich_dec.action == "PERSIST")

    # -- L10 META: know what you know and don't ----------------------------
    from .meta import known_unknowns, coverage, confidence
    ku_known = known_unknowns(mem, "credit stress crisis de-risk")
    ku_unknown = known_unknowns(mem, "unexplored alien-trading topic")
    out["l10_known"] = ku_known["status"]          # COVERED/THIN
    out["l10_unknown"] = ku_unknown["status"]      # UNKNOWN (go learn)
    out["l10_confidence"] = confidence(mem, "lesson", "crisis-1")["confidence"]
    out["l10_categories"] = len(coverage(mem))

    # -- L11 GUARD: memory says NO -----------------------------------------
    from .guard import guard_book
    g_block = guard_book(mem, CRISIS_FRAME, 0.55)   # naive book under stress
    out["l11_guards_naive"] = (g_block.verdict == "block")

    # -- L12 EXCHANGE: memory travels to a store that never lived it --------
    from .exchange import export_lesson, import_lesson
    _tmp = db.parent
    buyer = Memory(str(_tmp / "second-act-buyer.db"), tenant_id="buyer-brain")
    art = export_lesson(mem, "crisis-1")
    imp = import_lesson(buyer, art, credit_seller=mem)
    from .policy import is_stressed
    b_book = (de_risk_book(1, risk=1.0)
              if is_stressed(CRISIS_FRAME) and len(buyer.recall_lessons(
                  ["credit stress crisis"])) > 0
              else naive_book())
    out["l12_imported"] = (imp["verdict"] == "imported")
    out["l12_buyer_derisks"] = (b_book.equity < 0.10)
    buyer.close()

    # -- L13 CONSENSUS: agents agree on the truth ---------------------------
    from .consensus import agent_believe, reach_consensus
    a1 = Memory(str(_tmp / "second-act-cons-a.db"))
    a2 = Memory(str(_tmp / "second-act-cons-b.db"))
    agent_believe(a1, "regime", {"regime": "crisis", "equity_target": 0.05},
                  provenance={"source": "backtest", "evidence": 3,
                              "falsifiable": True, "hard": True})
    agent_believe(a2, "regime", {"regime": "calm", "equity_target": 0.55})
    consensus = reach_consensus([a1, a2], "regime")
    out["l13_consensus"] = consensus["status"]     # CONVERGED (conf wins)
    a1.close(); a2.close()

    # -- L14 CURRICULUM: memory schedules its own learning ------------------
    from .curriculum import learn_plan
    plan = learn_plan(mem, {"unexplored alien-trading topic": 0.9,
                            "credit stress crisis de-risk": 0.9})
    _p_unknown = [p for p in plan if p["status"] != "COVERED"][0]
    out["l14_plans_unknown"] = _p_unknown["topic"]

    # -- L15 DISTILL: scar tissue -> one generalizing capability ------------
    from .distill import decide_with_skill, distill_rule
    for i in range(3):
        mem.write_lesson(
            f"vol-scar-{i}",
            f"realized-vol crisis scar {i}: the loss was volatility, not credit",
            frame={"vix": 20.0, "credit_stress": 0.4, "realized_vol": 40.0},
            outcome={"max_drawdown": -0.2})
    _rule = distill_rule(mem)
    _novel = {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 55.0,
              "yield_slope": 0.5}
    _skill_book = decide_with_skill(mem, _novel)
    out["l15_rule_learned"] = _rule is not None
    out["l15_generalizes"] = (_skill_book.equity < 0.10)

    # -- L16 CONSENT: memory argues for its own life ------------------------
    from .consent import request_wipe, wipe_impact
    refuse = request_wipe(mem)                       # refuses silent wipe
    impact = wipe_impact(mem)
    out["l16_refuses"] = (not refuse["granted"])
    out["l16_impact_lessons"] = impact["lessons"]
    out["l16_wipe_hash"] = bool(impact["pre_wipe_content_hash"])

    # ---- the wipe: now a negotiated, audited act (L16) --------------------
    # L16 authorizes the destructive wipe with an explicit reason and journals
    # it to a store-independent log BEFORE the store is deleted.
    wipe = request_wipe(mem, force=True,
                        reason="spine demo: demonstrate the orphan/naive beat")
    out["l16_wiped"] = wipe["wiped"]
    out["wipe_audit"] = bool(wipe["audit_path"])
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
    L.append(f"   L7 self-anchored: {out.get('self_anchored')} "
             f"(anchor_resolves={out.get('anchor_resolves')})")
    L.append(f"   L8 supersession: prior={out.get('superseded_prior')} "
             f"chain_len={out.get('supersession_chain_len')}")
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
    L.append("   ==== SECOND ACT (L9-L16): what the field hasn't built ====")
    L.append(f"   L9 gate: noise_rejected={out['l9_noise_rejected']} "
             f"rich_persisted={out['l9_rich_persisted']}")
    L.append(f"   L10 meta: known={out['l10_known']} "
             f"unknown={out['l10_unknown']} conf={out['l10_confidence']} "
             f"cats={out['l10_categories']}")
    L.append(f"   L11 guard: guards_naive_0.55={out['l11_guards_naive']}")
    L.append(f"   L12 exchange: imported={out['l12_imported']} "
             f"buyer_derisks={out['l12_buyer_derisks']}")
    L.append(f"   L13 consensus: {out['l13_consensus']} (confidence wins)")
    L.append(f"   L14 curriculum: plans_unknown='{out['l14_plans_unknown']}'")
    L.append(f"   L15 distill: rule_learned={out['l15_rule_learned']} "
             f"generalizes_to_novel={out['l15_generalizes']}")
    L.append(f"   L16 consent: refuses_silent={out['l16_refuses']} "
             f"impact_lessons={out['l16_impact_lessons']} "
             f"hash={out['l16_wipe_hash']}")
    L.append("   >>> DELETE STORE (L16-audited) <<<")
    L.append(f"   wipe authorized: {out['l16_wiped']} audited={out['wipe_audit']}")
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
