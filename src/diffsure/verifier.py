"""Candidate verification from repository and independent checks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from diffsure.verification import CheckOutcome, CheckResult, CheckSpec, Evidence


class SandboxRunner(Protocol):
    def run(self, repository: Path, check: CheckSpec, timeout: float) -> CheckResult: ...


class CandidateVerifier:
    def __init__(self, sandbox: SandboxRunner, clock: Callable[[], float]) -> None:
        self.sandbox = sandbox
        self.clock = clock

    def verify(
        self,
        candidate_id: str,
        repository: Path,
        derived_checks: tuple[CheckSpec, ...],
        cutoff: float,
    ) -> Evidence:
        checks = (CheckSpec.repository_suite(), *derived_checks)
        results: list[CheckResult] = []
        for check in checks:
            remaining = cutoff - self.clock()
            if remaining <= 0:
                results.append(
                    CheckResult(
                        check.check_id,
                        check.kind,
                        CheckOutcome.TIMED_OUT,
                        None,
                        0.0,
                        "verification cutoff reached",
                    )
                )
                break
            result = self.sandbox.run(repository, check, remaining)
            results.append(result)
            if not result.passed:
                break
        return Evidence(candidate_id, tuple(results))
