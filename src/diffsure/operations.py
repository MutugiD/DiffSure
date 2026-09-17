"""Thread-safe service capacity, lifecycle, and operational metrics."""

from __future__ import annotations

import threading
from collections import Counter
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from enum import StrEnum
from types import TracebackType
from typing import Protocol

from diffsure.domain import SolveResponse


class SolverLike(Protocol):
    def solve(self, payload: object) -> SolveResponse: ...


class CapacityError(RuntimeError):
    """Raised when the service cannot admit another solve."""


class SolveState(StrEnum):
    RECEIVED = "received"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class SolveLifecycle:
    state: SolveState = SolveState.RECEIVED

    def transition(self, target: SolveState) -> None:
        allowed = {
            SolveState.RECEIVED: {SolveState.RUNNING, SolveState.CANCELLED},
            SolveState.RUNNING: {
                SolveState.COMPLETED,
                SolveState.FAILED,
                SolveState.CANCELLED,
            },
        }
        if target not in allowed.get(self.state, set()):
            raise ValueError(f"invalid solve transition: {self.state} -> {target}")
        self.state = target


class CapacityLease(AbstractContextManager[None]):
    def __init__(self, manager: CapacityManager) -> None:
        self.manager = manager
        self.acquired = False

    def __enter__(self) -> None:
        self.acquired = self.manager._acquire()
        if not self.acquired:
            raise CapacityError("service capacity is unavailable")

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.acquired:
            self.manager._release()


class CapacityManager:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._semaphore = threading.BoundedSemaphore(capacity)
        self._lock = threading.Lock()
        self._active = 0
        self._closing = False

    @property
    def available(self) -> int:
        with self._lock:
            return 0 if self._closing else self.capacity - self._active

    def admit(self) -> CapacityLease:
        return CapacityLease(self)

    def close(self) -> None:
        with self._lock:
            self._closing = True

    def _acquire(self) -> bool:
        with self._lock:
            if self._closing:
                return False
        if not self._semaphore.acquire(blocking=False):
            return False
        with self._lock:
            if self._closing:
                self._semaphore.release()
                return False
            self._active += 1
        return True

    def _release(self) -> None:
        with self._lock:
            self._active -= 1
        self._semaphore.release()


@dataclass(slots=True)
class OperationalMetrics:
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _counters: Counter[str] = field(default_factory=Counter)
    _phase_seconds: dict[str, float] = field(default_factory=dict)
    _elapsed_seconds: float = 0.0
    _input_tokens: int = 0
    _output_tokens: int = 0
    _estimated_cost_usd: float = 0.0

    def observe(self, response: SolveResponse) -> None:
        with self._lock:
            self._counters["requests"] += 1
            self._counters["diff"] += response.diff is not None
            self._counters["null"] += response.diff is None
            self._elapsed_seconds += response.usage.elapsed_seconds
            self._input_tokens += response.usage.input_tokens
            self._output_tokens += response.usage.output_tokens
            self._estimated_cost_usd += response.usage.estimated_cost_usd
            for item in response.record:
                phase = item.get("phase")
                if isinstance(phase, str):
                    self._counters[f"phase.{phase}"] += 1
                reason = item.get("reason")
                if reason in {"generation_cutoff", "delivery reserve reached"}:
                    self._counters["deadline_pressure"] += 1
                if phase == "candidate_gate":
                    self._counters["candidates"] += 1
                    candidate_id = item.get("candidate_id")
                    if isinstance(candidate_id, str) and "repair" in candidate_id:
                        self._counters["repairs"] += 1
                checks = item.get("checks")
                if isinstance(checks, list):
                    for check in checks:
                        if isinstance(check, dict) and isinstance(check.get("outcome"), str):
                            self._counters[f"check.{check['outcome']}"] += 1
                            elapsed = check.get("elapsed_seconds")
                            if isinstance(phase, str) and isinstance(elapsed, (int, float)):
                                self._phase_seconds[phase] = self._phase_seconds.get(
                                    phase, 0.0
                                ) + float(elapsed)

    def observe_fault(self) -> None:
        with self._lock:
            self._counters["requests"] += 1
            self._counters["fault"] += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(sorted(self._counters.items())),
                "phase_seconds": {
                    key: round(value, 6) for key, value in sorted(self._phase_seconds.items())
                },
                "elapsed_seconds": round(self._elapsed_seconds, 6),
                "input_tokens": self._input_tokens,
                "output_tokens": self._output_tokens,
                "estimated_cost_usd": round(self._estimated_cost_usd, 8),
            }


class ManagedSolver:
    def __init__(
        self, solver: SolverLike, capacity: CapacityManager, metrics: OperationalMetrics
    ) -> None:
        self.solver = solver
        self.capacity = capacity
        self.metrics = metrics

    def solve(self, payload: object) -> SolveResponse:
        lifecycle = SolveLifecycle()
        with self.capacity.admit():
            lifecycle.transition(SolveState.RUNNING)
            try:
                response = self.solver.solve(payload)
            except Exception:
                lifecycle.transition(SolveState.FAILED)
                self.metrics.observe_fault()
                raise
            lifecycle.transition(SolveState.COMPLETED)
            self.metrics.observe(response)
            return response
