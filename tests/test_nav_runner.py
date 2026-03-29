from __future__ import annotations

from tools.navigation.nav_runner import NavRunner


def test_next_returns_no_route_when_empty() -> None:
    runner = NavRunner([])
    assert runner.next() == "No route"


def test_next_advances_until_last_step_then_repeats_last() -> None:
    runner = NavRunner(["step 1", "step 2", "step 3"])

    assert runner.next() == "step 1"
    assert runner.next() == "step 2"
    assert runner.next() == "step 3"
    assert runner.next() == "step 3"
