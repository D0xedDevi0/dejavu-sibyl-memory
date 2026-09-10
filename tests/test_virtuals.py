"""Virtuals ACP stack tests.

Deterministic mock unit tests run in every environment.  Live integration
tests require ``DEJAVU_VIRTUALS_LIVE=1`` (and the acp CLI + signer) and
skip cleanly otherwise so the suite stays green in CI / on sandbox hosts.
"""

import pytest

from dejavu import virtuals

_HAS_ACP = virtuals.acp_available()


# ---- deterministic unit tests (always run) ---------------------------------

def test_agent_identity_constants():
    """The registered dejavu agent constants are present."""
    assert virtuals.DEJAVU_AGENT_ID.startswith("01a01184")
    assert virtuals.DEJAVU_WALLET.startswith("0xef25e214")
    assert virtuals.DEJAVU_SOLANA


def test_exercise_returns_identity_without_live_signer(monkeypatch):
    """exercise() returns the agent IDENTITY even when the live signer path
    is unavailable.  available must be False and error must explain why."""
    monkeypatch.delenv("DEJAVU_VIRTUALS_LIVE", raising=False)
    r = virtuals.exercise()
    # In a non-live environment the signer query fails, so available is False.
    assert r.available is False
    assert r.agent_id == virtuals.DEJAVU_AGENT_ID
    assert r.wallet == virtuals.DEJAVU_WALLET
    assert r.signer_policy is None
    assert "signer query failed" in (r.error or "")
    assert "DEJAVU_VIRTUALS_LIVE" in (r.error or "")


def test_run_sessions_surfaces_virtuals_identity(monkeypatch):
    """The full loop surfaces the Virtuals receipt even in dry/deterministic
    mode — the identity constants travel, available=False is honest."""
    monkeypatch.delenv("DEJAVU_VIRTUALS_LIVE", raising=False)
    import os
    import tempfile

    from dejavu.agent import run_sessions
    from dejavu.config import Config

    res = run_sessions(
        db_path=os.path.join(tempfile.mkdtemp(), "v.db"),
        config=Config(dry_run=True),
        virtuals=True,
    )
    assert res["virtuals"] is not None
    assert res["virtuals"]["agent_id"] == virtuals.DEJAVU_AGENT_ID
    assert res["virtuals"]["available"] is False
    assert res["virtuals"]["signer_policy"] is None


# ---- live integration tests (require DEJAVU_VIRTUALS_LIVE=1) ----------------

@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed or DEJAVU_VIRTUALS_LIVE not set (skip on CI)")
def test_acp_bin_path_exists():
    """The acp CLI binary should exist at the known path."""
    assert virtuals.acp_available()


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed or DEJAVU_VIRTUALS_LIVE not set (skip on CI)")
def test_exercise_returns_registered_agent():
    """exercise() returns the dejavu agent with a live signer policy."""
    r = virtuals.exercise()
    assert r.available is True
    assert r.agent_id == virtuals.DEJAVU_AGENT_ID
    assert r.wallet == virtuals.DEJAVU_WALLET
    assert r.signer_policy, "dejavu agent should have an active signer policy"
    assert r.signer_policy in ("ACP_ONLY", "restricted", "unrestricted", "deny-all")


@pytest.mark.skipif(not _HAS_ACP, reason="acp-cli not installed or DEJAVU_VIRTUALS_LIVE not set (skip on CI)")
def test_run_sessions_with_virtuals_live():
    """The full loop surfaces the Virtuals receipt when enabled."""
    import os
    import tempfile

    from dejavu.agent import run_sessions
    from dejavu.config import Config

    res = run_sessions(
        db_path=os.path.join(tempfile.mkdtemp(), "v.db"),
        config=Config(dry_run=True),
        virtuals=True,
    )
    assert res["virtuals"] is not None
    assert res["virtuals"]["available"] is True
    assert res["virtuals"]["wallet"] == virtuals.DEJAVU_WALLET