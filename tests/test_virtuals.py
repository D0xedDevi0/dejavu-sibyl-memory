"""Virtuals ACP stack tests (M4).

Requires the registered `echo` agent + `TS_KEYRING_BACKEND=file` (see
virtuals-echo-agent.md). Tests skip gracefully if the CLI isn't reachable so
the suite stays green in CI / on machines without the credentials.
"""

import pytest

from echo import virtuals

_HAS_ACP = virtuals.acp_available()


def test_agent_identity_constants():
    """The registered echo agent constants are present."""
    assert virtuals.ECHO_AGENT_ID.startswith("01a01184")
    assert virtuals.ECHO_WALLET.startswith("0xef25e214")
    assert virtuals.ECHO_SOLANA


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_acp_bin_path_exists():
    """The acp CLI binary should exist at the known path."""
    assert virtuals.acp_available()


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_exercise_returns_registered_agent():
    """exercise() returns the echo agent with a live signer policy."""
    r = virtuals.exercise()
    assert r.available is True
    assert r.agent_id == virtuals.ECHO_AGENT_ID
    assert r.wallet == virtuals.ECHO_WALLET
    assert r.signer_policy, "echo agent should have an active signer policy"
    assert r.signer_policy in ("ACP_ONLY", "restricted", "unrestricted", "deny-all")


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_run_sessions_with_virtuals():
    """The full loop surfaces the Virtuals receipt when enabled."""
    from echo.agent import run_sessions
    from echo.config import Config
    import os, tempfile
    res = run_sessions(db_path=os.path.join(tempfile.mkdtemp(), "v.db"),
                       config=Config(dry_run=True), virtuals=True)
    assert res["virtuals"] is not None
    assert res["virtuals"]["available"] is True
    assert res["virtuals"]["wallet"] == virtuals.ECHO_WALLET
