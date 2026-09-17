from __future__ import annotations

from diffsure.candidates import CandidateAttempt, FailureClass, rank_viable
from diffsure.providers import TokenUsage
from diffsure.verification import CheckKind, CheckOutcome, CheckResult, Evidence


def attempt(
    candidate_id: str,
    outcome: CheckOutcome = CheckOutcome.PASSED,
    *,
    elapsed: float = 1.0,
    diff: bytes = b"diff",
    static_error: str | None = None,
) -> CandidateAttempt:
    evidence = Evidence(
        candidate_id,
        (
            CheckResult("repo", CheckKind.REPOSITORY, outcome, 0, elapsed, "output"),
            CheckResult("derived", CheckKind.DERIVED, outcome, 0, elapsed, "output"),
        ),
    )
    return CandidateAttempt(candidate_id, None, diff, evidence, static_error, TokenUsage(), ())


def test_failure_classification() -> None:
    assert attempt("x", static_error="bad diff").failure_class is FailureClass.STRUCTURAL
    assert attempt("x", CheckOutcome.CANDIDATE_FAILED).failure_class is FailureClass.BEHAVIORAL
    assert attempt("x", CheckOutcome.TIMED_OUT).failure_class is FailureClass.RESOURCE
    assert (
        attempt("x", CheckOutcome.INFRASTRUCTURE_FAILED).failure_class
        is FailureClass.INFRASTRUCTURE
    )
    inconclusive = CandidateAttempt("x", None, b"", None, None, TokenUsage(), ())
    assert inconclusive.failure_class is FailureClass.INCONCLUSIVE
    assert attempt("x").failure_class is None


def test_ranking_prefers_evidence_runtime_size_then_stable_id() -> None:
    slow = attempt("candidate-1", elapsed=2)
    fast_large = attempt("candidate-2", elapsed=1, diff=b"longer")
    assert rank_viable([slow, fast_large]) is fast_large

    small_b = attempt("candidate-b", diff=b"a")
    small_a = attempt("candidate-a", diff=b"a")
    assert rank_viable([small_b, small_a]) is small_a
    assert rank_viable([attempt("failed", CheckOutcome.CANDIDATE_FAILED)]) is None
