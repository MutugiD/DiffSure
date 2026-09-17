"""Immutable wire and solve domain values."""

from __future__ import annotations

import re
from dataclasses import dataclass

REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RequestError(ValueError):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class SolveRequest:
    request_id: str
    repo_archive_b64: str
    task: str
    deadline_seconds: float

    @classmethod
    def from_dict(cls, value: object) -> SolveRequest:
        if not isinstance(value, dict):
            raise RequestError("request body must be an object")
        expected = {"request_id", "repo_archive_b64", "task", "deadline_seconds"}
        if set(value) != expected:
            raise RequestError("request fields do not match the solve contract")
        request_id = value["request_id"]
        archive = value["repo_archive_b64"]
        task = value["task"]
        deadline = value["deadline_seconds"]
        if not isinstance(request_id, str) or REQUEST_ID.fullmatch(request_id) is None:
            raise RequestError("request_id is invalid")
        if not isinstance(archive, str) or not archive:
            raise RequestError("repo_archive_b64 must be a nonempty string")
        if not isinstance(task, str) or not task.strip() or len(task) > 100_000:
            raise RequestError("task must be a nonempty string of at most 100000 characters")
        if isinstance(deadline, bool) or not isinstance(deadline, (int, float)):
            raise RequestError("deadline_seconds must be numeric")
        if not 1 <= float(deadline) <= 3600:
            raise RequestError("deadline_seconds must be between 1 and 3600")
        return cls(request_id, archive, task, float(deadline))


@dataclass(frozen=True, slots=True)
class Usage:
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass(frozen=True, slots=True)
class SolveResponse:
    request_id: str
    diff: str | None
    record: tuple[dict[str, object], ...]
    usage: Usage

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "diff": self.diff,
            "record": list(self.record),
            "usage": self.usage.as_dict(),
        }
