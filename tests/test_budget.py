from __future__ import annotations

import pytest

from diffsure.budget import SolveBudget


class Clock:
    value = 100.0

    def __call__(self) -> float:
        return self.value


def test_budget_cutoffs_and_remaining() -> None:
    clock = Clock()
    budget = SolveBudget.start(200, clock)
    assert budget.reserve_seconds == 20
    assert budget.candidate_cutoff == 217
    assert budget.repair_cutoff == 253
    assert budget.usable_cutoff == 280
    assert budget.can_generate()
    clock.value = 220
    assert not budget.can_generate()
    assert budget.can_repair()
    assert budget.remaining(budget.repair_cutoff) == 33
    clock.value = 400
    assert budget.remaining() == 0


def test_budget_reserve_bounds() -> None:
    assert SolveBudget.start(50, lambda: 0).reserve_seconds == 10
    assert SolveBudget.start(600, lambda: 0).reserve_seconds == 30
    with pytest.raises(ValueError):
        SolveBudget.start(5, lambda: 0)
