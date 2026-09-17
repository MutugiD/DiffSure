from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from diffsure.domain import SolveResponse
from diffsure.providers import ModelTurn, ToolCall
from diffsure.solve import VerifiedPatchSolver
from diffsure.verification import CheckOutcome, CheckResult, CheckSpec
from tests.test_solve import PATCH, ScriptedProvider, payload, repository_archive, settings


class QueueProvider:
    name = "fake"
    model = "queue"

    def __init__(self, turns: list[ModelTurn]) -> None:
        designer = ScriptedProvider().complete([], [], 1)
        self.turns = [designer, *turns]

    def complete(self, messages, tools, timeout):  # type: ignore[no-untyped-def]
        return self.turns.pop(0)


def valid_turns() -> list[ModelTurn]:
    return [
        ModelTurn(tool_calls=(ToolCall("patch", "apply_patch", {"diff": PATCH}),)),
        ModelTurn("done"),
    ]


class SequenceSandbox:
    def __init__(
        self,
        outcomes: list[CheckOutcome],
        elapsed: list[float] | None = None,
        on_call: Callable[[int], None] | None = None,
    ) -> None:
        self.outcomes = outcomes
        self.elapsed = elapsed or [0.1] * len(outcomes)
        self.calls = 0
        self.on_call = on_call

    def run(self, repository: Path, check: CheckSpec, timeout: float) -> CheckResult:
        self.calls += 1
        if self.on_call is not None:
            self.on_call(self.calls)
        outcome = self.outcomes.pop(0)
        return CheckResult(
            check.check_id, check.kind, outcome, 0, self.elapsed.pop(0), "counterexample"
        )


def selected(response: SolveResponse) -> str | None:
    events = [item for item in response.record if item.get("phase") == "selection"]
    value = events[-1]["candidate_id"]
    return value if isinstance(value, str) else None


def test_failed_lineages_can_be_repaired(tmp_path: Path) -> None:
    provider = QueueProvider([*valid_turns(), *valid_turns(), ModelTurn("repair")])
    sandbox = SequenceSandbox(
        [
            CheckOutcome.CANDIDATE_FAILED,
            CheckOutcome.CANDIDATE_FAILED,
            CheckOutcome.CANDIDATE_FAILED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
        ]
    )
    response = VerifiedPatchSolver(settings(), provider, sandbox).solve(
        payload(repository_archive(tmp_path))
    )
    assert response.diff is not None
    assert selected(response) == "candidate-1-repair-1"


def test_second_candidate_wins_when_first_is_structurally_invalid(tmp_path: Path) -> None:
    provider = QueueProvider([ModelTurn("no patch"), *valid_turns()])
    sandbox = SequenceSandbox(
        [
            CheckOutcome.CANDIDATE_FAILED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
            CheckOutcome.PASSED,
        ]
    )
    response = VerifiedPatchSolver(settings(), provider, sandbox).solve(
        payload(repository_archive(tmp_path))
    )
    assert response.diff is not None
    assert selected(response) == "candidate-2"


def test_weaker_later_candidate_does_not_replace_stronger_one(tmp_path: Path) -> None:
    provider = QueueProvider([*valid_turns(), *valid_turns()])
    sandbox = SequenceSandbox(
        [CheckOutcome.CANDIDATE_FAILED, *([CheckOutcome.PASSED] * 6)],
        [0.1, 0.1, 0.1, 2.0, 2.0, 0.1, 0.1],
    )
    response = VerifiedPatchSolver(settings(), provider, sandbox).solve(
        payload(repository_archive(tmp_path))
    )
    assert response.diff is not None
    assert selected(response) == "candidate-1"


def test_generation_cutoff_returns_already_verified_candidate(tmp_path: Path) -> None:
    now = [0.0]

    def advance(call: int) -> None:
        if call == 3:
            now[0] = 71.0

    provider = QueueProvider(valid_turns())
    sandbox = SequenceSandbox(
        [CheckOutcome.CANDIDATE_FAILED, *([CheckOutcome.PASSED] * 4)],
        on_call=advance,
    )
    response = VerifiedPatchSolver(settings(), provider, sandbox, clock=lambda: now[0]).solve(
        payload(repository_archive(tmp_path))
    )
    assert response.diff is not None
    assert selected(response) == "candidate-1"
    assert not provider.turns
