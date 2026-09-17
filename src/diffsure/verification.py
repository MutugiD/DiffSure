"""Immutable verification specifications and observed evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath


class CheckKind(StrEnum):
    REPOSITORY = "repository"
    DERIVED = "derived"


class CheckOutcome(StrEnum):
    PASSED = "passed"
    CANDIDATE_FAILED = "candidate_failed"
    INFRASTRUCTURE_FAILED = "infrastructure_failed"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class DerivedFile:
    path: str
    content: bytes

    def __post_init__(self) -> None:
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or not path.parts
            or "." in path.parts
            or ".." in path.parts
            or "\\" in self.path
        ):
            raise ValueError("derived file path must be safe and relative")
        if len(self.content) > 1_000_000:
            raise ValueError("derived file exceeds the size limit")


@dataclass(frozen=True, slots=True)
class CheckSpec:
    check_id: str
    kind: CheckKind
    command: str
    files: tuple[DerivedFile, ...] = ()

    def __post_init__(self) -> None:
        if re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", self.check_id) is None:
            raise ValueError("check_id is invalid")
        if not self.command.strip() or "\x00" in self.command or len(self.command) > 4096:
            raise ValueError("check command is invalid")
        if self.kind is CheckKind.REPOSITORY and self.files:
            raise ValueError("repository checks cannot contain derived files")

    @classmethod
    def repository_suite(cls) -> CheckSpec:
        return cls("repository-suite", CheckKind.REPOSITORY, "bash run_tests.sh")


@dataclass(frozen=True, slots=True)
class CheckResult:
    check_id: str
    kind: CheckKind
    outcome: CheckOutcome
    exit_code: int | None
    elapsed_seconds: float
    output: str

    @property
    def passed(self) -> bool:
        return self.outcome is CheckOutcome.PASSED


@dataclass(frozen=True, slots=True)
class Evidence:
    candidate_id: str
    results: tuple[CheckResult, ...]

    @property
    def viable(self) -> bool:
        kinds = {result.kind for result in self.results if result.passed}
        return (
            CheckKind.REPOSITORY in kinds
            and CheckKind.DERIVED in kinds
            and all(result.passed for result in self.results)
        )
