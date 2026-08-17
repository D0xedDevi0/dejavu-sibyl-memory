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
