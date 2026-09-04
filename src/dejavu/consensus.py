"""L13 — CONSENSUS: a fleet of agents agrees on what is true.

L8 resolves conflicts *inside one store* (a contradiction is superseded, never
blindly overwritten). L13 is the cross-agent generalization: when INDEPENDENT
agents (each with their own store) hold DIFFERING beliefs about the same topic,
who decides? Memory products don't — each store is a walled garden, so a team
of agents either never converges or last-writer-wins with no notion of who to
trust.

THE SPINE's L13 gives the shared truth a decision procedure grounded in L10's
per-store confidence:

    reach_consensus(stores, topic) -> a reconciled belief.

Rule set (deterministic, no LLM):
  UNANIMOUS   all stores agree -> that claim wins outright.
  CONVERGED   disagreement, but one claim is backed by confidence >= quorum
              (decision-grade, provenance-backed) -> it wins; the dissenting
              lower-confidence claims are journaled as DISSENT (never silently
              dropped, never force-equal).
  MAJORITY    no claim clears the quorum, but a strict majority holds one
              claim -> it wins (majority, honestly labelled).
  DEADLOCK    a genuine split with no confidence signal and no majority ->
              NO winner is fabricated. The topic is recorded CONTESTED so a
              downstream agent knows it is unresolved and must learn, not guess.

Load-bearing mirrors:
  1. A lone low-confidence dissenting view (conf 0.3) does NOT overturn a
     high-confidence, provenance-backed hard lesson (conf 0.85). The converged
     value is the credible one — noise doesn't move the truth.
  2. A genuine unknown split (two ~0.35 claims disagreeing) returns DEADLOCK,
     not a fabricated winner — the fleet refuses a false consensus, exactly as
     L10 refuses to hallucinate coverage and L8 refuses to silently overwrite.

The reconciled belief is written to a coordinator/consensus store as a
decision-grade entity + journaled, so a downstream agent cold-starting from the
shared truth inherits what the fleet actually agreed on.
"""

from __future__ import annotations

import json
from typing import Any

from .meta import confidence

# A claim backed by this L10 confidence is 'decision-grade' and wins outright.
QUORUM = 0.60
BELIEF_CATEGORY = "belief"      # each agent stores its belief here: (topic, claim)
CONSENSUS_CATEGORY = "consensus"  # coordinator writes the reconciled truth here


def _claim_of(body: Any) -> dict | None:
    if isinstance(body, dict) and isinstance(body.get("claim"), dict):
        return body["claim"]
    if isinstance(body, dict):
        return body
    return None


def _fingerprint(claim: dict) -> str:
    return json.dumps(claim, sort_keys=True, separators=(",", ":"), default=str)


def agent_believe(memory, topic: str, claim: dict, *,
                  provenance: dict | None = None) -> dict:
    """An agent records its belief on `topic`. `claim` is the propositional,
    comparable value (e.g. {'equity_target': 0.05}). Optional provenance drives
    L10 confidence — call record_provenance separately, or pass `hard` here."""
    body = {"claim": claim, "topic": topic}
    if provenance:
        from .meta import record_provenance
        record_provenance(memory, BELIEF_CATEGORY, topic,
                          source=provenance.get("source"),
                          evidence=int(provenance.get("evidence", 0)),
                          falsifiable=bool(provenance.get("falsifiable")),
                          hard=bool(provenance.get("hard")))
    return memory.set_entity(BELIEF_CATEGORY, topic, body, status="active")


def reach_consensus(stores: list, topic: str, *,
                    quorum: float = QUORUM,
                    consensus_memory=None) -> dict:
    """Reconcile independent agent stores' beliefs on `topic`.

    Args:
        stores: list of Memory handles, one per independent agent.
        topic: the disputed belief name (each store's entity is
               (BELIEF_CATEGORY, topic)).
        quorum: L10 confidence a claim needs to win outright.
        consensus_memory: optional Memory where the reconciled belief is written
               (category CONSENSUS_CATEGORY). If None, only the verdict returns.

    Returns a dict with status UNANIMOUS/CONVERGED/MAJORITY/DEADLOCK, the
    winning claim (or None on DEADLOCK), per-agent votes, and dissent.
    """
    votes: list[dict] = []
    for st in stores:
        ent = None
        try:
            ent = st.get_entity(BELIEF_CATEGORY, topic)
        except Exception:
            ent = None
        if ent is None:
            continue  # abstain — no belief on this topic
        body = ent.get("body")
        claim = _claim_of(body)
        if claim is None:
            continue
        conf = confidence(st, BELIEF_CATEGORY, topic)
        votes.append({
            "owner": st.tenant_id, "claim": claim, "body": body,
            "confidence": conf["confidence"], "conf_reason": conf["reason"],
        })
    if not votes:
        result = {"status": "DEADLOCK", "topic": topic, "votes": [],
                  "reason": "no agent holds a belief on this topic",
                  "converged": None}
        return result

    # Group by normalized claim fingerprint.
    groups: dict[str, dict] = {}
    for v in votes:
        fp = _fingerprint(v["claim"])
        g = groups.setdefault(fp, {"claim": v["claim"], "votes": [],
                                   "max_conf": 0.0, "total_conf": 0.0})
        g["votes"].append(v)
        g["max_conf"] = max(g["max_conf"], v["confidence"])
        g["total_conf"] += v["confidence"]
    ordered = sorted(groups.values(), key=lambda g: -g["max_conf"])

    if len(ordered) == 1:
        status = "UNANIMOUS"
        winner = ordered[0]
        reason = "all agents agree"
    else:
        top = ordered[0]
        n = len(votes)
        if top["max_conf"] >= quorum:
            status = "CONVERGED"
            winner = top
            reason = (f"confidence-backed: max {top['max_conf']:.2f} >= "
                      f"quorum {quorum:.2f}")
        elif len(top["votes"]) > n / 2.0:
            status = "MAJORITY"
            winner = top
            reason = f"strict majority ({len(top['votes'])}/{n}) without quorum"
        else:
            status = "DEADLOCK"
            winner = None
            reason = ("genuine split: no quorum and no majority — refusing to "
                      "fabricate a winner")
    dissent = [v for v in votes
               if winner is not None and _fingerprint(v["claim"]) != _fingerprint(winner["claim"])]

    result = {
        "status": status, "topic": topic,
        "votes": votes, "dissent": dissent, "reason": reason,
        "converged": winner["claim"] if winner is not None else None,
        "converged_confidence": round(winner["max_conf"], 3) if winner else None,
    }

    # Persist the reconciled truth into the coordinator store (decision-grade).
    if consensus_memory is not None and status != "DEADLOCK":
        consensus_memory.set_entity(CONSENSUS_CATEGORY, topic, {
            "claim": winner["claim"], "status": status, "reason": reason,
            "owners": [v["owner"] for v in winner["votes"]],
            "dissenting": [v["owner"] for v in dissent],
        }, status="active")
        from .meta import record_provenance
        record_provenance(consensus_memory, CONSENSUS_CATEGORY, topic,
                          source="fleet-consensus",
                          evidence=len(winner["votes"]),
                          falsifiable=True, hard=(status in ("UNANIMOUS", "CONVERGED")))
        consensus_memory.write_event(
            evaluated={"topic": topic, "votes": [v["owner"] for v in votes]},
            acted={"status": status, "converged": winner["claim"]},
            forward="downstream",
            extra={"dissent": [v["owner"] for v in dissent]})
    elif consensus_memory is not None:
        # No fabricated consensus: record CONTESTED so downstream knows.
        consensus_memory.set_entity(CONSENSUS_CATEGORY, topic, {
            "claim": None, "status": "CONTESTED", "reason": reason,
            "owners": [v["owner"] for v in votes],
        }, status="active")
        consensus_memory.write_event(
            evaluated={"topic": topic},
            acted={"status": "CONTESTED", "reason": reason},
            forward="downstream", extra={})
    return result
