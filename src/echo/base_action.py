"""Onchain leg for the echo loop (Base). Wired in M3 of the build window.

The memory-driven decision produces a Book; this module turns it into a REAL
Base transaction (x402 payment or wallet operation) and returns a tx hash for
the demo. Until M3, `execute` runs in dry-run and returns a receipt struct.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import Config


@dataclass
class OnchainReceipt:
    dry_run: bool
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    tx_hash: str | None = None
    explorer_url: str | None = None

    def as_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "action": self.action,
            "details": self.details,
            "tx_hash": self.tx_hash,
            "explorer_url": self.explorer_url,
        }


def execute(book, config: Config) -> OnchainReceipt:
    """Turn a Book into an onchain action on Base.

    M3: when a real x402 / wallet-op path is confirmed, replace the dry-run
    body with an actual broadcast. `dry_run` keeps this safe until then.
    """
    # Memory-driven decision -> what the wallet should do.
    if book.equity <= 0.05:
        action = "x402_payment_de_risk"
        details = {"mode": "de-risk", "equity_target": book.equity}
    else:
        action = "x402_payment_hold"
        details = {"mode": "hold", "equity_target": book.equity}

    if config.dry_run:
        return OnchainReceipt(
            dry_run=True, action=action, details=details,
            tx_hash=None, explorer_url=None,
        )

    # TODO(M3): broadcast real tx using config.rpc_url, wallet_key, escrow.
    raise NotImplementedError("M3 wires the real Base transaction here.")
