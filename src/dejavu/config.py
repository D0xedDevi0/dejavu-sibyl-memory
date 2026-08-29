"""Paths, defaults, and onchain config for the dejavu loop.

Central place for anything the agent needs at runtime. Kept import-light so
tests and the demo can inject overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Repo root = two levels up from this file (src/dejavu/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB = DATA_DIR / "memory.db"

# Base onchain leg (M3). Values from project memory / verified live.
BASE_RPC = "https://mainnet.base.org"
AGENT_WALLET_KEY = Path(os.environ.get(
    "DEJAVU_WALLET_KEY", str(Path.home() / ".secrets" / "agent-wallet.key")
))
X402_ESCROW = "0x8AEE621035D93Deb3C0C1177fac252dC2dd501a0"
FEE_RECIPIENT = "0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83"
BASE_EXPLORER = "https://basescan.org/tx/"


@dataclass
class Config:
    db_path: Path = DEFAULT_DB
    rpc_url: str = BASE_RPC
    wallet_key: Path = AGENT_WALLET_KEY
    x402_escrow: str = X402_ESCROW
    fee_recipient: str = FEE_RECIPIENT
    dry_run: bool = field(default_factory=lambda: os.environ.get("DEJAVU_DRY_RUN", "1") != "0")  # 0 -> broadcast real tx
    search_phrases: tuple[str, ...] = field(
        default_factory=lambda: (
            "credit stress crisis lesson",
            "drawdown loss recovery",
        )
    )
    # Stress thresholds that flip the policy (load-bearing trigger).
    credit_stress_threshold: float = 0.7
    vix_threshold: float = 30.0

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
