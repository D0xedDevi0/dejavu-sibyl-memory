"""NEURAL_MESH x Sibyl Memory — the memory-dejavu loop (`dejavu`).

An autonomous agent whose onchain (Base) decisions are *driven by* its own
persistent memory. Core thesis: "Forgetting is a bug. Remembering is the
strategy."

Submodules:
    memory.py     — Sibyl wrapper (write / recall / search, all five tiers)
    policy.py     — decide_differently, the LOAD-BEARING decision function
    agent.py      — orchestration loop (session A learns -> session B cold-starts)
    config.py     — paths, wallet, RPC
    base_action.py— onchain leg (x402 / wallet op) — wired in M3
"""

__version__ = "0.1.0"
