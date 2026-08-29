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


def test_real_signing_constructs_valid_tx():
    """Sign the real dust transfer locally (no broadcast) to prove the path."""
    if not os.path.exists("/opt/data/.secrets/agent-wallet.key"):
        pytest.skip("agent wallet key not present")
    cfg = Config(dry_run=True)
    acct = _load_account(cfg)
    tx = {
        "to": acct.address, "value": 1000, "gas": 21000,
        "gasPrice": 1, "nonce": 0, "chainId": 8453,
    }
    signed = acct.sign_transaction(tx)
    assert signed.hash  # a deterministic, broadcastable signed tx
    # The from-address derived from the signature must match our wallet.
    from eth_account import Account as _Acc
    assert _Acc.recover_transaction(signed.raw_transaction) == acct.address
