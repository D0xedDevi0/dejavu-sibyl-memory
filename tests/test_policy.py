"""Policy-layer tests: decide_differently behaves correctly at the boundary."""

from echo.memory import Memory
from echo.policy import decide_differently, is_stressed, naive_book


def test_calm_market_no_memory_naive():
    m = Memory("/tmp/__echo_policy_calm.db")
    b = decide_differently({"vix": 18.0, "credit_stress": 0.3}, m)
    assert b.equity == naive_book().equity
    m.delete_store()


def test_stressed_with_lesson_de_risks():
    import os, tempfile
    db = os.path.join(tempfile.mkdtemp(), "memory.db")
    m = Memory(db)
    m.write_lesson("t", "When stressed, de-risk to cash.", frame={"vix": 52.0})
    b = decide_differently({"vix": 52.0, "credit_stress": 2.2}, m)
    assert b.equity <= 0.05
    m.delete_store()


def test_stressed_no_memory_naive():
    import os, tempfile
    db = os.path.join(tempfile.mkdtemp(), "memory.db")
    m = Memory(db)
    b = decide_differently({"vix": 52.0, "credit_stress": 2.2}, m)
    assert b.equity > 0.5  # stressed but no recall -> stays long
    m.delete_store()


def test_memory_none_is_naive_even_if_stressed():
    b = decide_differently({"vix": 52.0, "credit_stress": 2.2}, None)
    assert b.equity > 0.5  # no memory object at all -> fail open


def test_is_stressed_boundary():
    assert is_stressed({"vix": 31.0, "credit_stress": 0.1})
    assert is_stressed({"vix": 10.0, "credit_stress": 0.8})
    assert not is_stressed({"vix": 25.0, "credit_stress": 0.5})


# ---- MacroBench regime substrate (ranked #2, handle D0xedDevi0) ----------
from echo.policy import RISK_OFF, deploy_from_risk, macrobench_sleeves, risk_score


def test_risk_score_rises_with_stress():
    calm = {"vix": 15.0, "credit_stress": 0.2, "realized_vol": 10.0}
    crisis = {"vix": 60.0, "credit_stress": 2.5, "realized_vol": 45.0}
    assert risk_score(calm) < 0.3
    assert risk_score(crisis) > 0.8  # caps at 0.9 with healthy yield slope


def test_macrobench_sleeves_match_ranked_book():
    """The de-risk arm reuses the real RISK_OFF defensive book."""
    crisis = {"vix": 60.0, "credit_stress": 2.5, "realized_vol": 45.0}
    r = risk_score(crisis)
    sleeves = macrobench_sleeves(r)
    # At high crisis the book collapses toward the defensive sleeve:
    # equity collapses toward the RISK_OFF floor, rates+hedges dominate.
    assert sleeves[2] <= 0.05            # equity near zero
    assert sleeves[5] + sleeves[4] > sleeves[2]  # rates+hedges > equity
    # Deployed exactly at deploy_from_risk (0.97 only at calm; lower in crisis).
    assert abs(sum(sleeves) - deploy_from_risk(r)) < 0.01
    assert max(sleeves) <= max(RISK_OFF) + 0.01  # never exceeds a sleeve's cap
