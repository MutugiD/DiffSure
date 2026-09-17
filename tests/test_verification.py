from __future__ import annotations

import pytest

from diffsure.verification import (
    CheckKind,
    CheckOutcome,
    CheckResult,
    CheckSpec,
    DerivedFile,
    Evidence,
)


def result(kind: CheckKind, outcome: CheckOutcome = CheckOutcome.PASSED) -> CheckResult:
    return CheckResult("check", kind, outcome, 0, 0.1, "ok")


def test_repository_suite_contract() -> None:
    check = CheckSpec.repository_suite()
    assert check.command == "bash run_tests.sh"
    assert check.kind is CheckKind.REPOSITORY


@pytest.mark.parametrize("path", ["/absolute", "../escape", "a/../escape", r"a\b"])
def test_derived_file_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(ValueError):
        DerivedFile(path, b"test")


def test_check_spec_validation() -> None:
    with pytest.raises(ValueError):
        CheckSpec("INVALID", CheckKind.DERIVED, "true")
    with pytest.raises(ValueError):
        CheckSpec("valid", CheckKind.DERIVED, "")
    with pytest.raises(ValueError):
        CheckSpec("repo", CheckKind.REPOSITORY, "true", (DerivedFile("x", b"x"),))


def test_evidence_requires_all_checks_and_both_kinds() -> None:
    assert Evidence("one", (result(CheckKind.REPOSITORY), result(CheckKind.DERIVED))).viable
    assert not Evidence("one", (result(CheckKind.REPOSITORY),)).viable
    assert not Evidence(
        "one",
        (
            result(CheckKind.REPOSITORY),
            result(CheckKind.DERIVED, CheckOutcome.CANDIDATE_FAILED),
        ),
    ).viable
