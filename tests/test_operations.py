from __future__ import annotations

import threading

import pytest

from diffsure.domain import SolveResponse, Usage
from diffsure.operations import (
    CapacityError,
    CapacityManager,
    ManagedSolver,
    OperationalMetrics,
    SolveLifecycle,
    SolveState,
)


def response(diff: str | None = "diff") -> SolveResponse:
    return SolveResponse(
        "id",
        diff,
        (
            {
                "phase": "candidate_gate",
                "candidate_id": "candidate-1-repair-1",
                "checks": [
                    {"outcome": "passed", "elapsed_seconds": 0.5},
                ],
            },
        ),
        Usage("fake", "model", 3, 2, 0.1, 1.5),
    )


def test_capacity_admission_and_close() -> None:
    manager = CapacityManager(1)
    with manager.admit():
        assert manager.available == 0
        with pytest.raises(CapacityError), manager.admit():
            pass
    assert manager.available == 1
    manager.close()
    assert manager.available == 0
    with pytest.raises(CapacityError), manager.admit():
        pass


def test_lifecycle_rejects_invalid_transition() -> None:
    lifecycle = SolveLifecycle()
    lifecycle.transition(SolveState.RUNNING)
    lifecycle.transition(SolveState.COMPLETED)
    with pytest.raises(ValueError):
        lifecycle.transition(SolveState.RUNNING)


def test_metrics_capture_outcomes_phases_usage_and_cost() -> None:
    metrics = OperationalMetrics()
    metrics.observe(response())
    metrics.observe(response(None))
    metrics.observe_fault()
    value = metrics.snapshot()
    counters = value["counters"]
    assert isinstance(counters, dict)
    assert counters["requests"] == 3
    assert counters["diff"] == 1
    assert counters["null"] == 1
    assert counters["repairs"] == 2
    assert value["input_tokens"] == 6
    assert value["estimated_cost_usd"] == 0.2
    assert value["phase_seconds"] == {"candidate_gate": 1.0}


def test_managed_solver_releases_capacity_after_fault() -> None:
    class Broken:
        def solve(self, payload: object) -> SolveResponse:
            raise RuntimeError

    capacity = CapacityManager(1)
    metrics = OperationalMetrics()
    managed = ManagedSolver(Broken(), capacity, metrics)
    with pytest.raises(RuntimeError):
        managed.solve({})
    assert capacity.available == 1
    counters = metrics.snapshot()["counters"]
    assert isinstance(counters, dict)
    assert counters["fault"] == 1


def test_three_capacity_leases_can_be_active_together() -> None:
    manager = CapacityManager(3)
    barrier = threading.Barrier(3)
    active: list[int] = []

    def worker() -> None:
        with manager.admit():
            active.append(manager.available)
            barrier.wait(timeout=2)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)
    assert not any(thread.is_alive() for thread in threads)
    assert 0 in active
    assert manager.available == 3
