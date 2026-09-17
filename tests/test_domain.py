from __future__ import annotations

import pytest

from diffsure.domain import RequestError, SolveRequest, SolveResponse, Usage

VALID = {
    "request_id": "request-1",
    "repo_archive_b64": "value",
    "task": "fix it",
    "deadline_seconds": 180,
}


def test_request_parses_exact_contract() -> None:
    request = SolveRequest.from_dict(VALID)
    assert request.request_id == "request-1"
    assert request.deadline_seconds == 180.0


@pytest.mark.parametrize(
    "value",
    [
        [],
        {**VALID, "extra": True},
        {**VALID, "request_id": "bad id"},
        {**VALID, "repo_archive_b64": ""},
        {**VALID, "task": " "},
        {**VALID, "deadline_seconds": True},
        {**VALID, "deadline_seconds": 0},
        {**VALID, "deadline_seconds": 3601},
    ],
)
def test_request_rejects_invalid_contract(value: object) -> None:
    with pytest.raises(RequestError):
        SolveRequest.from_dict(value)


def test_response_serializes_contract() -> None:
    usage = Usage("ollama", "model", 1, 2, 0.0, 0.5)
    response = SolveResponse("id", None, ({"role": "assistant"},), usage).as_dict()
    assert response["request_id"] == "id"
    assert response["diff"] is None
    assert response["usage"] == usage.as_dict()
