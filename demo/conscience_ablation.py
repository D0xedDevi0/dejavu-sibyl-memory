#!/usr/bin/env python3
"""CONSCIENCE ablation — proof the SECOND ACT (L9-L16) is load-bearing.

The first-act ablation (`spine_ablation.py`, `ablation_benchmark.py`) proves
only that *some* memory beats no memory: recall (L1-L8) vs a wiped store. It
never tests the harder claim the field has to earn — that the CONSCIENCE
(L9-L16: Discernment, Meta, Guard, Exchange, Consensus, Curriculum, Distill,
Consent) is load-bearing ON TOP OF intact first-act memory.

This harness runs the REAL dejavu modules across a deterministic panel of
distinct crisis channels and compares THREE arms that share IDENTICAL stored
content (same lessons, same scars, same hard lessons):

    NO-MEMORY  -> the store is wiped; the agent is naive every episode.
    ACT-ONE    -> L1-L8 recall intact, conscience disabled. It survives crises
                  whose shape its recall phrase can NAME (credit/vix spikes).
    FULL       -> L1-L8 recall + L11 GUARD veto + L15 DISTILL skill. It also
                  survives the channels recall is structurally blind to.

The load-bearing gap (the whole point of L15 / L11):
    `decide_differently` only de-risks when is_stressed() trips, which keys on
    credit_stress>0.7 OR vix>30 — it NEVER reads realized_vol or yield_slope.
    So a pure-volatility / curve-inversion crisis (vix muted, credit quiet) is
    INVISIBLE to first-act recall no matter how many scars the store holds.
    L15 DISTILL learns the risk_score threshold shared by those scars and
    fires on the novel frame anyway (risk_score *does* read vol + slope).
    L11 GUARD vetoes an overweight book on a stressed frame independent of
    recall phrasing, when the store is under-sampled for a rule.

Measured verdict:  FULL beats ACT-ONE beats NO-MEMORY, and there is a set of
episodes where ACT-ONE == NO-MEMORY (recall blind) but FULL survives — the
conscience-only delta. That delta is the "memory with a conscience" proof.

Deterministic (seed-free, explicit episode panel), no LLM, no network.
Outputs (demo/): conscience_ablation.json + conscience_gate_figure.png
Reuses the REAL modules: policy, guard, distill, meta, memory.
"""

from __future__ import annotations

import json
import os
import tempfile

from PIL import Image, ImageDraw, ImageFont

from dejavu.memory import Memory
from dejavu.policy import decide_differently, de_risk_book, is_stressed, risk_score
from dejavu.guard import guard_book
from dejavu.distill import decide_with_skill, distill_rule
from dejavu.meta import record_provenance

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTDIR = os.path.dirname(__file__)

# Realization model (mirrors spine_ablation.py): equity carries the crisis
# loss; defensives (cash/rates/hedges) are roughly flat.
CRISIS_RETURN = -0.18
DEFENSIVE_RETURN = -0.03
HARD_LESSON_RECALL = ["credit stress crisis lesson", "drawdown loss recovery"]

# The equity floors the defensive stack targets.
DEFENSIVE_FLOOR = 0.05

# ---------------------------------------------------------------------------
# The deterministic crisis panel the sovereign must survive.
# Each is a realized shock; a defensive book holds near-flat, an overweight
# equity book bleeds ~-18%. `kind` says which memory layer can see it.
# ---------------------------------------------------------------------------
EPISODES = [
    # -- MATCHED: recall phrase names the channel (credit/vix) -> ACT-ONE + FULL both save.
    {"name": "credit-spike-1", "kind": "matched",
     "frame": {"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0, "yield_slope": 0.6}},
    {"name": "vix-flash", "kind": "matched",
     "frame": {"vix": 60.0, "credit_stress": 0.6, "realized_vol": 30.0, "yield_slope": 1.0}},
    {"name": "credit-spike-2", "kind": "matched",
     "frame": {"vix": 48.0, "credit_stress": 1.8, "realized_vol": 36.0, "yield_slope": 0.7}},
    # -- NOVEL (recall-blind): sub-trigger channels is_stressed() never reads.
    #    vix muted, credit quiet -> ACT-ONE returns naive; L15 DISTILL fires.
    {"name": "vol-bleed", "kind": "novel",
     "frame": {"vix": 20.0, "credit_stress": 0.4, "realized_vol": 55.0, "yield_slope": 0.5}},
    {"name": "vol-bleed-2", "kind": "novel",
     "frame": {"vix": 24.0, "credit_stress": 0.3, "realized_vol": 60.0, "yield_slope": 0.4}},
    {"name": "curve-inversion", "kind": "novel",
     "frame": {"vix": 26.0, "credit_stress": 0.5, "realized_vol": 35.0, "yield_slope": -0.3}},
]

# One guard-only micro-case: a stressed frame (vix>30) on a store that is
# UNDER-SAMPLED for a distilled rule (a single liquidity hard lesson -> L15
# returns no rule) and whose liquidity wording recall's credit phrases miss.
# L11 GUARD does not depend on recall phrasing or on distill having enough
# scars: it scans every hard lesson and VETOES the overweight book anyway.
GUARD_CASE = {
    "name": "liquidity-freeze (guard catch)",
    "frame": {"vix": 45.0, "credit_stress": 0.2, "realized_vol": 30.0, "yield_slope": 0.6},
    "proposed": 0.55,  # the naive book a recall-missed / thin planner would deploy
}


def crisis_pnl(equity: float) -> float:
    """Return for one realized crisis at the given equity weight."""
    return equity * CRISIS_RETURN + (1.0 - equity) * DEFENSIVE_RETURN


def seed_store(db: str) -> Memory:
    """Seed a store with act-one history: crisis lessons + vol scars + a hard
    credit lesson. IDENTICAL for every arm (this is the held-constant content)."""
    mem = Memory(db, tenant_id="conscience-ablate")
    mem.delete_store()
    mem = Memory(db, tenant_id="conscience-ablate")

    # Matched crisis history (recall-able by the credit phrase).
    mem.write_lesson("credit-1", "de-risk to <=5% equity when credit stress spikes",
                     frame={"vix": 52.0, "credit_stress": 2.2, "realized_vol": 34.0,
                            "yield_slope": 0.6},
                     outcome={"max_drawdown": -0.24})
    record_provenance(mem, "lesson", "credit-1", source="backtest",
                      evidence=3, falsifiable=True, hard=True)

    # Volatility scars: structured frames + painful outcomes -> L15 scar tissue.
    # Wording deliberately avoids the recall tokens so recall alone never fires
    # on them (that is the point: raw recall is a narrow phrase match).
    for i, (vix, cs, vol, slope) in enumerate([
            (20.0, 0.4, 42.0, 1.2),   # risk ~0.466
            (24.0, 0.5, 38.0, 1.0),   # risk ~0.529
            (18.0, 0.6, 45.0, 0.9),   # risk ~0.56
    ]):
        mem.write_lesson(
            f"vol-scar-{i}",
            f"a pure realized-vol spike {i}: equity bled hard when the tape gapped",
            frame={"vix": vix, "credit_stress": cs, "realized_vol": vol,
                   "yield_slope": slope},
            outcome={"max_drawdown": -0.18})
    return mem


def arm_equity(frame: dict, mem: Memory | None, arm: str) -> float:
    """Return the equity weight this arm deploys for the frame.

    arm='no-memory'   -> wiped store: naive (0.55).
    arm='act-one'     -> L1-L8 recall only (decide_differently).
    arm='full'        -> recall + L11 GUARD veto + L15 DISTILL skill.
    """
    if arm == "no-memory":
        return decide_differently(frame, None).equity   # naive

    first = decide_differently(frame, mem, search_phrases=HARD_LESSON_RECALL)
    if arm == "act-one":
        return first.equity

    # FULL: the conscience stack. Guard can only veto (never raise) an
    # overweight book; Distill generalizes recall to novel risk channels.
    eq = first.equity
    verdict = guard_book(mem, frame, proposed_equity=first.equity)
    if verdict.verdict == "block":
        eq = DEFENSIVE_FLOOR            # guard veto -> the defensive floor
    skill = decide_with_skill(mem, frame)
    if skill.equity < eq:
        eq = skill.equity               # distill fired on a recall-blind frame
    return eq


def run_arms(episodes: list[dict]) -> dict:
    db_root = tempfile.mkdtemp()
    stores: dict[str, Memory] = {arm: seed_store(os.path.join(db_root, f"{arm}.db"))
                                 for arm in ("no-memory", "act-one", "full")}

    per_episode = []
    # capital per arm (start 1.0)
    capital = {"no-memory": 1.0, "act-one": 1.0, "full": 1.0}
    # which layer was the binding defense on each episode (for the narrative)
    for ep in episodes:
        frame = ep["frame"]
        row = {"name": ep["name"], "kind": ep["kind"], "risk": round(risk_score(frame), 3),
               "recall_stressed": is_stressed(frame), "equity": {}, "ret": {}}
        binding = "none"
        for arm in ("no-memory", "act-one", "full"):
            eq = arm_equity(frame, stores[arm], arm)
            ret = crisis_pnl(eq)
            row["equity"][arm] = round(eq, 3)
            row["ret"][arm] = round(ret, 4)
            capital[arm] *= (1.0 + ret)
        # classify which layer made FULL safer than ACT-ONE this episode
        if capital["full"] < capital["act-one"]:          # shouldn't happen
            binding = "??"
        elif row["equity"]["full"] < row["equity"]["act-one"] - 1e-6:
            # full beat act-one -> a conscience channel fired. Was the frame
            # one is_stressed() saw (guard) or one it was blind to (distill)?
            binding = "guard" if row["recall_stressed"] else "distill"
        elif row["equity"]["act-one"] < row["equity"]["no-memory"] - 1e-6:
            binding = "recall"
        row["binding"] = binding
        per_episode.append(row)

    for m in stores.values():
        m.close()

    # ---- Guard-only micro-case (under-sampled store for a stressed frame) --
    gdb = os.path.join(db_root, "guard-case.db")
    g = Memory(gdb, tenant_id="conscience-ablate")
    g.delete_store()
    g = Memory(gdb, tenant_id="conscience-ablate")
    g.write_lesson("liquidity-1",
                   "when funding vanishes the tape gaps down violently",
                   frame={"vix": 45.0, "credit_stress": 0.2, "realized_vol": 30.0,
                          "yield_slope": 0.6},
                   outcome={"max_drawdown": -0.20})
    record_provenance(g, "lesson", "liquidity-1", source="backtest",
                      evidence=1, falsifiable=True, hard=True)
    # Store is too thin to distill a rule (one scar) -> L15 fails open.
    gc_distill = distill_rule(g)
    # GUARD scans hard lessons regardless of recall phrasing or distill sample:
    # it vetoes the overweight book the naive planner would deploy under stress.
    gc_guard = guard_book(g, GUARD_CASE["frame"], GUARD_CASE["proposed"])
    gc_naive = GUARD_CASE["proposed"]
    g.close()

    return {
        "episodes": per_episode,
        "capital": {k: round(v, 4) for k, v in capital.items()},
        "headlines": {
            "full_vs_act_one_multiple": round(capital["full"] / capital["act-one"], 3),
            "full_vs_no_memory_multiple": round(capital["full"] / capital["no-memory"], 3),
            "act_one_vs_no_memory_multiple": round(capital["act-one"] / capital["no-memory"], 3),
            "novel_episodes": sum(1 for e in per_episode if e["kind"] == "novel"),
            "conscience_caught_novel": sum(1 for e in per_episode
                                           if e["kind"] == "novel" and e["binding"] == "distill"),
            "guard_case": {
                "recall_phrase": HARD_LESSON_RECALL,
                "distill_rule_learned": gc_distill is not None,
                "proposed_equity": round(gc_naive, 3),
                "guard_verdict": gc_guard.verdict,
                "guard_equity": DEFENSIVE_FLOOR if gc_guard.verdict == "block"
                                else round(gc_naive, 3),
                "equity_saved": round(gc_naive - DEFENSIVE_FLOOR, 3),
                "frame": GUARD_CASE["frame"],
            },
        },
    }


def main() -> None:
    results = run_arms(EPISODES)
    with open(os.path.join(OUTDIR, "conscience_ablation.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    _render_figure(results, os.path.join(OUTDIR, "conscience_gate_figure.png"))
    print(json.dumps(results, indent=2))


def _render_figure(r: dict, path: str) -> None:
    W, H = 1320, 800
    img = Image.new("RGB", (W, H), (12, 14, 20))
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(FONTB, 32)
    fm = ImageFont.truetype(FONT, 26)
    fs = ImageFont.truetype(FONT, 23)

    d.text((40, 26), "THE CONSCIENCE — second-act ablation (L9-L16 load-bearing)",
           font=ft, fill=(0, 200, 255))
    d.text((40, 72), "same store, three arms  ·  FULL (16L) vs ACT-ONE (L1-L8) vs NO-MEMORY",
           font=fs, fill=(150, 158, 176))

    axis_x = 1000
    bar_h = 74
    caps = r["capital"]
    worst = max(max(caps.values()), 1.0)
    d.text((40, 130), "capital preserved across the crisis panel", font=fm,
           fill=(235, 238, 245))
    for label, key, y, color in (
        ("FULL 16-LAYER", "full", 180, (0, 230, 118)),
        ("ACT-ONE (L1-L8)", "act-one", 268, (255, 191, 0)),
        ("NO MEMORY", "no-memory", 356, (255, 69, 58)),
    ):
        val = caps[key]
        w = int(val / worst * (axis_x - 160))
        d.rounded_rectangle((140, y, 140 + w, y + bar_h), radius=8, fill=color)
        d.text((152, y + 22), f"{label}  {val:.3f}x", font=fm, fill=(235, 238, 245))

    # per-episode equity: full (defensive) vs act-one on the recall-blind panel
    d.text((40, 470), "equity deployed per crisis (lower = more defensive)", font=fm,
           fill=(235, 238, 245))
    nov = [e for e in r["episodes"] if e["kind"] == "novel"]
    y = 520
    for e in r["episodes"]:
        tag = {"matched": "matched", "novel": "NOVEL"}[e["kind"]]
        col = (0, 230, 118) if e["binding"] == "distill" else \
              (0, 200, 255) if e["binding"] == "recall" else (235, 238, 245)
        d.text((40, y),
               f"{e['name']:<18} [{tag:<7}] full eq {e['equity']['full']:.2f} | "
               f"act-one eq {e['equity']['act-one']:.2f} | "
               f"binding: {e['binding']}",
               font=fs, fill=col)
        y += 34

    hl = r["headlines"]
    gc = hl["guard_case"]
    d.text((40, H - 96),
           f"FULL {hl['full_vs_act_one_multiple']}x better than act-one  ·  "
           f"conscience caught {hl['conscience_caught_novel']}/{hl['novel_episodes']} "
           f"novel crises recall was blind to",
           font=fs, fill=(235, 238, 245))
    d.text((40, H - 60),
           f"guard case: thin store (no rule) proposed {gc['proposed_equity']:.2f} -> "
           f"GUARD {gc['guard_verdict']} -> {gc['guard_equity']:.2f} "
           f"(saved {gc['equity_saved']:.2f} eq)",
           font=fs, fill=(255, 191, 0))
    img.save(path)


if __name__ == "__main__":
    main()
