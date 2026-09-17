"""Candidate lineage, failure classification, and deterministic ranking."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from diffsure.providers import TokenUsage
from diffsure.verification import CheckOutcome, Evidence


class FailureClass(StrEnum):
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    RESOURCE = "resource"
    INFRASTRUCTURE = "infrastructure"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class CandidateAttempt:
    candidate_id: str
    parent_id: str | None
    diff: bytes
    evidence: Evidence | None
    static_error: str | None
    usage: TokenUsage
    record: tuple[dict[str, object], ...]

    @property
    def viable(self) -> bool:
        return self.static_error is None and self.evidence is not None and self.evidence.viable

    @property
    def failure_class(self) -> FailureClass | None:
        if self.viable:
            return None
        if self.static_error is not None:
            return FailureClass.STRUCTURAL
        if self.evidence is None or not self.evidence.results:
            return FailureClass.INCONCLUSIVE
        outcomes = {result.outcome for result in self.evidence.results}
        if CheckOutcome.INFRASTRUCTURE_FAILED in outcomes:
            return FailureClass.INFRASTRUCTURE
        if CheckOutcome.TIMED_OUT in outcomes:
            return FailureClass.RESOURCE
        if CheckOutcome.CANDIDATE_FAILED in outcomes:
            return FailureClass.BEHAVIORAL
        return FailureClass.INCONCLUSIVE


def rank_viable(attempts: list[CandidateAttempt]) -> CandidateAttempt | None:
    viable = [attempt for attempt in attempts if attempt.viable]
    if not viable:
        return None
    return min(viable, key=_rank_key)


def _rank_key(attempt: CandidateAttempt) -> tuple[int, float, int, str]:
    assert attempt.evidence is not None
    passed = sum(result.passed for result in attempt.evidence.results)
    runtime = sum(result.elapsed_seconds for result in attempt.evidence.results)
    return (-passed, runtime, len(attempt.diff), attempt.candidate_id)
