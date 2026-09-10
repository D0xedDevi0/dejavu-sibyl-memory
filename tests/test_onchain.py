"""Onchain leg tests (M3).

Dry-run is the default and must never touch the network. These tests also
verify the real-signing path constructs a valid, signable tx (no broadcast).
"""

import os

import pytest

from dejavu.agent import run_sessions, session_b
from dejavu.base_action import _load_account, _transaction_target, execute
from dejavu.config import Config
from dejavu.memory import Memory


def _tmp_config(**kw) -> Config:
    return Config(dry_run=True, **kw)


def test_execute_dry_run_no_network():
    """Dry-run must not hit RPC and returns no tx hash."""
    cfg = _tmp_config()
    class _B:
        equity = 0.05
        rationale = "recalled lesson"
    r = execute(_B(), cfg)
    assert r.dry_run is True
    assert r.tx_hash is None
    assert r.action == "de_risk"


def test_execute_hold_action_for_naive():
    class _B:
        equity = 0.55
        rationale = "naive"
    r = execute(_B(), _tmp_config())
    assert r.action == "hold"
    assert r.dry_run is True


def test_de_risk_and_hold_have_distinct_transaction_targets():
    sender = "0x23129c0472172D75bEd1e6dd061301796760Ecd9"
    recipient = "0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83"
    assert _transaction_target("de_risk", sender, recipient) == recipient
    assert _transaction_target("hold", sender, recipient) == sender


def test_run_sessions_includes_onchain_receipt():
    res = run_sessions(db_path=os.path.join("/tmp", "echo_oc_test.db"),
                       config=_tmp_config())
    assert "onchain" in res
    assert res["onchain"]["dry_run"] is True
    assert res["onchain"]["action"] == "de_risk"  # crisis + memory -> de-risk


def test_real_signing_constructs_valid_tx(tmp_path):
    """Sign and recover with an ephemeral key — no real wallet needed.

    Uses an on-the-fly generated private key that lives only for this test.
    Never touches any production secret on disk."""
    from eth_account import Account as _Acc

    key_path = tmp_path / "ephemeral.key"
    acct = _Acc.create()
    key_path.write_text(acct.key.hex())

    cfg = Config(dry_run=True, wallet_key=key_path)
    loaded = _load_account(cfg)
    assert loaded.address == acct.address

    tx = {
        "to": acct.address, "value": 1000, "gas": 21000,
        "gasPrice": 1, "nonce": 0, "chainId": 8453,
    }
    signed = loaded.sign_transaction(tx)
    assert signed.hash  # a deterministic, broadcastable signed tx
    assert _Acc.recover_transaction(signed.raw_transaction) == acct.address
