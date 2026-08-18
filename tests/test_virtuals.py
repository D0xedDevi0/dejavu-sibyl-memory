"""Virtuals ACP stack tests (M4).

Requires the registered `dejavu` agent + `TS_KEYRING_BACKEND=file` (see
virtuals-dejavu-agent.md). Tests skip gracefully if the CLI isn't reachable so
the suite stays green in CI / on machines without the credentials.
"""

import pytest

from dejavu import virtuals

_HAS_ACP = virtuals.acp_available()


def test_agent_identity_constants():
    """The registered dejavu agent constants are present."""
    assert virtuals.DEJAVU_AGENT_ID.startswith("01a01184")
    assert virtuals.DEJAVU_WALLET.startswith("0xef25e214")
    assert virtuals.DEJAVU_SOLANA


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_acp_bin_path_exists():
    """The acp CLI binary should exist at the known path."""
    assert virtuals.acp_available()


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_exercise_returns_registered_agent():
    """exercise() returns the dejavu agent with a live signer policy."""
    r = virtuals.exercise()
    assert r.available is True
    assert r.agent_id == virtuals.DEJAVU_AGENT_ID
    assert r.wallet == virtuals.DEJAVU_WALLET
    assert r.signer_policy, "dejavu agent should have an active signer policy"
    assert r.signer_policy in ("ACP_ONLY", "restricted", "unrestricted", "deny-all")


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed (skip on CI)")
def test_run_sessions_with_virtuals():
    """The full loop surfaces the Virtuals receipt when enabled."""
    from dejavu.agent import run_sessions
    from dejavu.config import Config
    import os, tempfile
    res = run_sessions(db_path=os.path.join(tempfile.mkdtemp(), "v.db"),
                       config=Config(dry_run=True), virtuals=True)
    assert res["virtuals"] is not None
    assert res["virtuals"]["available"] is True
    assert res["virtuals"]["wallet"] == virtuals.DEJAVU_WALLET
