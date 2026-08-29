"""Onchain leg for the dejavu loop (Base Mainnet).

The memory-driven decision (a Book) becomes a REAL Base transaction. Two modes
used in the demo:

  * `de_risk`  (recalled a crisis lesson) -> transfer dust ETH to the fee
    recipient, labelled a de-risk / hedge settlement. Tx hash is the proof the
    agent *acted onchain because it remembered*.
  * `hold`     (no stress / naive)         -> a dust self-transfer (keep-alive).

`execute()` defaults to dry-run for safety. Set `dry_run=False` (env
`DEJAVU_DRY_RUN=0`, or `Config(dry_run=False)`) to broadcast a real tx.

Verified live (2026-08-17):
  * RPC mainnet.base.org  -> chainId 0x2105 (8453)
  * agent wallet 0x23129c0472172D75bEd1e6dd061301796760Ecd9, ~5e-05 ETH, 409 prior txs
  * gas price ~0.006 gwei (Base is cheap; a dust transfer costs fractions of a cent)
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from eth_account import Account
from eth_account.datastructures import SignedTransaction

from .config import BASE_EXPLORER, Config

_RPC_HEADERS = {"Content-Type": "application/json", "User-Agent": "curl/8"}
DUST = 1_000  # wei; a symbolic, near-free amount (transaction, not value, is the point)


def _is_valid_address(a: str) -> bool:
    return (isinstance(a, str) and len(a) == 42 and a.startswith("0x")
            and all(c in "0123456789abcdefABCDEF" for c in a[2:]))


def _transaction_target(action: str, sender: str, fee_recipient: str) -> str:
    """Return an onchain-distinct target for each policy branch."""
    if action == "de_risk":
        if not _is_valid_address(fee_recipient):
            raise ValueError("de_risk requires a valid fee recipient address")
        return fee_recipient
    return sender


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


def _rpc(url: str, method: str, params: list) -> Any:
    req = urllib.request.Request(
        url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                              "params": params}).encode(),
        headers=_RPC_HEADERS,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())["result"]


def _load_account(config: Config) -> Account:
    raw = config.wallet_key.read_text().strip()
    if not raw.startswith("0x"):
        raw = "0x" + raw
    return Account.from_key(raw)


def _broadcast(url: str, signed: SignedTransaction) -> str:
    raw_hex = "0x" + signed.raw_transaction.hex()
    req = urllib.request.Request(
        url, data=json.dumps({"jsonrpc": "2.0", "id": 1,
                              "method": "eth_sendRawTransaction",
                              "params": [raw_hex]}).encode(),
        headers=_RPC_HEADERS,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())["result"]


def execute(book, config: Config) -> OnchainReceipt:
    """Turn a Book into an onchain action on Base Mainnet.

    With memory (de-risk) the agent moves dust to the fee recipient — an actual
    executed transaction. The tx hash is the demo's "it didn't just remember, it
    acted" proof.
    """
    action = "de_risk" if book.equity <= 0.05 else "hold"
    details = {"equity_target": round(book.equity, 3),
               "rationale": book.rationale}

    # ---- dry-run: no broadcast, everything else simulated ----------------
    if config.dry_run:
        return OnchainReceipt(
            dry_run=True, action=action, details=details,
            tx_hash=None, explorer_url=None,
        )

    # ---- real broadcast --------------------------------------------------
    acct = _load_account(config)
    to = _transaction_target(action, acct.address, config.fee_recipient)
    chain_id = int(_rpc(config.rpc_url, "eth_chainId", []), 16)
    nonce = int(_rpc(config.rpc_url, "eth_getTransactionCount", [acct.address, "latest"]), 16)
    gas_price = int(_rpc(config.rpc_url, "eth_gasPrice", []), 16)
    gas_limit = 21000

    tx = {
        "to": to,
        "value": DUST,
        "gas": gas_limit,
        "gasPrice": gas_price,
        "nonce": nonce,
        "chainId": chain_id,
    }
    signed = acct.sign_transaction(tx)
    tx_hash = _broadcast(config.rpc_url, signed)
    explorer = BASE_EXPLORER.rstrip("/") + "/" + tx_hash

    details.update({
        "from": acct.address, "to": to, "value_wei": DUST,
        "chain_id": chain_id, "nonce": nonce, "gas_price_gwei": round(gas_price / 1e9, 4),
    })
    return OnchainReceipt(
        dry_run=False, action=action, details=details,
        tx_hash=tx_hash, explorer_url=explorer,
    )
