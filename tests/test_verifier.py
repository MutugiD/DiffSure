from __future__ import annotations

from pathlib import Path

from diffsure.verification import CheckKind, CheckOutcome, CheckResult, CheckSpec
from diffsure.verifier import CandidateVerifier


class Sandbox:
    def __init__(self, outcomes: list[CheckOutcome]) -> None:
        self.outcomes = outcomes
        self.checks: list[CheckSpec] = []

    def run(self, repository: Path, check: CheckSpec, timeout: float) -> CheckResult:
        self.checks.append(check)
        outcome = self.outcomes.pop(0)
        return CheckResult(check.check_id, check.kind, outcome, 0, 0.1, "result")


def test_verifies_repository_before_derived_check(tmp_path: Path) -> None:
    sandbox = Sandbox([CheckOutcome.PASSED, CheckOutcome.PASSED])
    verifier = CandidateVerifier(sandbox, lambda: 1.0)
    derived = CheckSpec("derived", CheckKind.DERIVED, "true")
    evidence = verifier.verify("candidate-1", tmp_path, (derived,), 10)
    assert [check.kind for check in sandbox.checks] == [CheckKind.REPOSITORY, CheckKind.DERIVED]
    assert evidence.viable


def test_stops_after_failure(tmp_path: Path) -> None:
    sandbox = Sandbox([CheckOutcome.CANDIDATE_FAILED])
    verifier = CandidateVerifier(sandbox, lambda: 1.0)
    derived = CheckSpec("derived", CheckKind.DERIVED, "true")
    evidence = verifier.verify("candidate-1", tmp_path, (derived,), 10)
    assert len(sandbox.checks) == 1
    assert not evidence.viable


def test_records_exhausted_cutoff_without_running(tmp_path: Path) -> None:
    sandbox = Sandbox([])
    verifier = CandidateVerifier(sandbox, lambda: 10.0)
    evidence = verifier.verify("candidate-1", tmp_path, (), 10)
    assert evidence.results[0].outcome is CheckOutcome.TIMED_OUT
    assert not sandbox.checks
