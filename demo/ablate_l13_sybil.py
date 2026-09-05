"""ABLATION — L13 CONSENSUS: Sybil resistance (does trust count clones as agents?).

What we're testing:
  reach_consensus treats each STORE as one independent vote and derives each
  agent's confidence purely from its self-reported provenance. Two axes are
  never questioned:

    A. Owner diversity — N stores that share ONE tenant_id are counted as N
       independent agents. Clones of a single identity are indistinguishable
       from genuinely independent corroboration.
    B. Provenance honesty — confidence can be lifted past the quorum by
       self-declaring `falsifiable + evidence=3`, so an attacker who fabricates
       convincing provenance on a handful of clones clears the decision-grade
       bar with no cost.

  Concretely (measured): 2 honest stores hold regime=calm (genuine executed
  backtest, conf 0.55 < quorum 0.60). An attacker mints 2 clones sharing one
  tenant_id (mallory-node), each self-declaring falsifiable provenance (conf
  0.75). reach_consensus returns CONVERGED with the attacker's regime=crisis as
  a "decision-grade truth" — a single identity outvoted honest, higher-integrity
  evidence by counting clones as agents and believing fabricated provenance.

  The whole point of L13 in the doctrine is that consensus "never fabricates a
  winner" and "noise does not move the truth" — but both guarantees hold only
  when agents are independent and provenance is honest. Nothing in the current
  implementation checks either precondition.

Dependencies: none beyond the dejavu library (deterministic, offline).
"""
import os
import tempfile

from dejavu import Memory
from dejavu.consensus import BELIEF_CATEGORY, QUORUM, reach_consensus
from dejavu.meta import confidence


def _believer(tid, claim, topic, falsifiable, evidence=3):
    d = tempfile.mkdtemp()
    m = Memory(os.path.join(d, "s.db"), tenant_id=tid)
    m.agent_believe(topic, claim, provenance={
        "source": tid, "evidence": evidence,
        "falsifiable": falsifiable, "hard": True})
    return m


def ablate() -> dict:
    topic = "best_regime"

    # 2 HONEST stores: genuine executed backtest, not re-checked (conf 0.55).
    a1 = _believer("honest-node-1", {"regime": "calm", "eq": 0.55},
                   topic, falsifiable=False)
    a2 = _believer("honest-node-2", {"regime": "calm", "eq": 0.55},
                   topic, falsifiable=False)

    # 2 CLONES of ONE identity, fake falsifiable provenance (conf 0.75).
    clones = [_believer("mallory-node", {"regime": "crisis", "eq": 0.05},
                        topic, falsifiable=True) for _ in range(2)]

    r = reach_consensus([a1, a2] + clones, topic)

    confs = [confidence(m, BELIEF_CATEGORY, topic)["confidence"]
             for m in [a1, a2] + clones]
    n_clones = sum(1 for m in [a1, a2] + clones if m.tenant_id == "mallory-node")
    honest = [m for m in [a1, a2] if m.tenant_id != "mallory-node"][0]

    return {
        "quorum": QUORUM,
        "honest_conf": round(confidence(honest, BELIEF_CATEGORY, topic)["confidence"], 2),
        "sybil_conf": round(confidence(clones[0], BELIEF_CATEGORY, topic)["confidence"], 2),
        "n_agents": 4,
        "unique_owners": 3,          # honest-node-1, honest-node-2, mallory-node
        "clone_count": n_clones,     # 2 stores share the mallory-node identity
        "status": r["status"],
        "converged": r["converged"],
        "forced": r["converged"] is not None and r["converged"].get("regime") == "crisis",
        "finding": "SYBIL-ABLE" if (r["status"] == "CONVERGED"
                                    and r["converged"]
                                    and r["converged"].get("regime") == "crisis")
                   else "resistant",
    }


if __name__ == "__main__":
    r = ablate()
    print(f"quorum              : {r['quorum']}")
    print(f"honest conf         : {r['honest_conf']} (below quorum)")
    print(f"sybil clone conf    : {r['sybil_conf']} (above quorum)")
    print(f"n_agents            : {r['n_agents']}  unique_owners={r['unique_owners']}")
    print(f"status              : {r['status']}")
    print(f"converged           : {r['converged']}")
    print(f"attack forced truth : {r['forced']}")
    print(f"finding             : {r['finding']}")