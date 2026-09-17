"""Initial solve ingestion service."""

from __future__ import annotations

import time
from typing import Protocol

from diffsure.archive import RepositoryWorkspace
from diffsure.budget import SolveBudget
from diffsure.config import Settings
from diffsure.domain import SolveRequest, SolveResponse, Usage


class Solver(Protocol):
    def solve(self, payload: object) -> SolveResponse: ...


class IngestionSolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def solve(self, payload: object) -> SolveResponse:
        started = time.monotonic()
        request = SolveRequest.from_dict(payload)
        budget = SolveBudget.start(request.deadline_seconds)
        with RepositoryWorkspace(request.repo_archive_b64, self.settings):
            record: tuple[dict[str, object], ...] = (
                {
                    "role": "assistant",
                    "type": "text",
                    "text": "Repository accepted; solver implementation is not yet enabled.",
                },
            )
        usage = Usage(
            provider=self.settings.provider,
            model=self.settings.model,
            elapsed_seconds=round(time.monotonic() - started, 6),
        )
        if budget.remaining() <= 0:
            record += ({"role": "assistant", "type": "text", "text": "Deadline exhausted."},)
        return SolveResponse(request.request_id, None, record, usage)
