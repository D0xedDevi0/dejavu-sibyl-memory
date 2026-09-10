"""Virtuals ACP stack for the dejavu loop.

The `dejavu` agent is a registered, signer-enabled Virtuals Protocol agent
(ACP_ONLY policy — it can transact onchain autonomously). This module surfaces
that coordination layer so the memory-dejavu loop is driven by a Virtuals agent
identity as well as Sibyl Memory + Base.

See `virtuals-dejavu-agent.md` at repo root for full credentials + the critical
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
DEJAVU_AGENT_ID = "01a01184-784b-7989-9d10-526fcb708ebd"
DEJAVU_WALLET = "0xef25e2144f7ca887a9dc59e732c9e23e6a5847bb"
DEJAVU_SOLANA = "8oaYbfWCzFxqnrEN3yFGGcVwX6hKFBCQkkzEqRU4fjWa"


@dataclass
class VirtualsReceipt:
    available: bool
    agent_id: str
    wallet: str
    solana_wallet: str
    name: str = "dejavu"
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
    """True only when the acp CLI is present AND the caller has explicitly
    opted into live Virtuals integration via DEJAVU_VIRTUALS_LIVE=1."""
    return (ACP_BIN.exists()
            and shutil.which(str(ACP_BIN)) is not None
            and os.environ.get("DEJAVU_VIRTUALS_LIVE") == "1")


def check_signer() -> dict | None:
    """Query the dejavu agent's signer policy (proves it can transact)."""
    if not acp_available():
        return None
    try:
        r = subprocess.run(
            [str(ACP_BIN), "agent", "signer-policy", "--agent-id", DEJAVU_AGENT_ID, "--json"],
            capture_output=True, text=True, timeout=60, env=_env(),
        )
        out = r.stdout.strip()
        return json.loads(out) if out else None
    except Exception:
        return None


def exercise() -> VirtualsReceipt:
    """Coordinate the loop through the Virtuals dejavu agent identity.

    ``available`` is True only when the acp CLI IS present AND the live
    Virtuals integration is opted-in AND the signer query succeeds.  Without
    all three, ``available`` is False and the error field explains why —
    the agent identity constants still surface so callers can record the
    identity even when the live signer path is unavailable."""
    signer = check_signer()
    return VirtualsReceipt(
        available=signer is not None,
        agent_id=DEJAVU_AGENT_ID,
        wallet=DEJAVU_WALLET,
        solana_wallet=DEJAVU_SOLANA,
        signer_policy=(signer or {}).get("policy"),
        error=(
            None if signer
            else "signer query failed "
                 "(set DEJAVU_VIRTUALS_LIVE=1 and TS_KEYRING_BACKEND=file for live path)"
        ),
        details={"signer": signer},
    )
