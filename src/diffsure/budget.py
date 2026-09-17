"""Monotonic solve budget."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolveBudget:
    started: float
    deadline: float
    candidate_cutoff: float
    repair_cutoff: float
    usable_cutoff: float
    reserve_seconds: float
    clock: Callable[[], float]

    @classmethod
    def start(cls, duration: float, clock: Callable[[], float] = time.monotonic) -> SolveBudget:
        started = clock()
        reserve = min(30.0, max(10.0, duration * 0.10))
        usable = duration - reserve
        if usable <= 0:
            raise ValueError("deadline leaves no usable solve interval")
        return cls(
            started=started,
            deadline=started + duration,
            candidate_cutoff=started + usable * 0.65,
            repair_cutoff=started + usable * 0.85,
            usable_cutoff=started + usable,
            reserve_seconds=reserve,
            clock=clock,
        )

    def remaining(self, cutoff: float | None = None) -> float:
        return max(0.0, (self.deadline if cutoff is None else cutoff) - self.clock())

    def can_generate(self) -> bool:
        return self.clock() < self.candidate_cutoff

    def can_repair(self) -> bool:
        return self.clock() < self.repair_cutoff
