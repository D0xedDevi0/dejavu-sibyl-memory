"""Virtuals ACP stack for the echo loop.

The `echo` agent is a registered, signer-enabled Virtuals Protocol agent
(ACP_ONLY policy — it can transact onchain autonomously). This module surfaces
that coordination layer so the memory-echo loop is driven by a Virtuals agent
identity as well as Sibyl Memory + Base.

See `virtuals-echo-agent.md` at repo root for full credentials + the critical
`TS_KEYRING_BACKEND=file` fix.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ACP_BIN = Path("/opt/data/acp-cli/node_modules/.bin/acp")
ACP_CONFIG_DIR = Path("/opt/data/.acp")
ECHO_AGENT_ID = "01a01184-784b-7989-9d10-526fcb708ebd"
ECHO_WALLET = "0xef25e2144f7ca887a9dc59e732c9e23e6a5847bb"
ECHO_SOLANA = "8oaYbfWCzFxqnrEN3yFGGcVwX6hKFBCQkkzEqRU4fjWa"


@dataclass
class VirtualsReceipt:
    available: bool
    agent_id: str
    wallet: str
    solana_wallet: str
    name: str = "echo"
    signer_policy: str | None = None
    error: str | None = None
    details: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "available": self.available,
            "name": self.name,
            "agent_id": self.agent_id,
            "wallet": self.wallet,
            "solana_wallet": self.solana_wallet,
            "signer_policy": self.signer_policy,
            "error": self.error,
            "details": self.details,
        }


def _env() -> dict:
    env = dict(os.environ)
    env["TS_KEYRING_BACKEND"] = "file"
    env["ACP_CONFIG_DIR"] = str(ACP_CONFIG_DIR)
    return env


def acp_available() -> bool:
    return ACP_BIN.exists() and shutil.which(str(ACP_BIN)) is not None


def check_signer() -> dict | None:
    """Query the echo agent's signer policy (proves it can transact)."""
    if not acp_available():
        return None
    try:
        r = subprocess.run(
            [str(ACP_BIN), "agent", "signer-policy", "--agent-id", ECHO_AGENT_ID, "--json"],
            capture_output=True, text=True, timeout=60, env=_env(),
        )
        out = r.stdout.strip()
        return json.loads(out) if out else None
    except Exception:
        return None


def exercise() -> VirtualsReceipt:
    """Coordinate the loop through the Virtuals echo agent identity."""
    signer = check_signer()
    return VirtualsReceipt(
        available=True,
        agent_id=ECHO_AGENT_ID,
        wallet=ECHO_WALLET,
        solana_wallet=ECHO_SOLANA,
        signer_policy=(signer or {}).get("policy"),
        error=None if signer else "signer query failed (check TS_KEYRING_BACKEND=file)",
        details={"signer": signer},
    )
