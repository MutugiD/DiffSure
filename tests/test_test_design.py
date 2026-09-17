from __future__ import annotations

import base64
import json

import pytest

from diffsure.providers.base import ModelTurn, ProviderError, TokenUsage
from diffsure.providers.base import Provider as ProviderProtocol
from diffsure.test_design import IndependentTestDesigner


class Provider:
    name = "fake"
    model = "fixture"

    def __init__(self, text: str) -> None:
        self.text = text
        self.messages: list[dict[str, object]] = []

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn:
        self.messages = messages
        assert tools == []
        assert timeout == 5
        return ModelTurn(self.text, usage=TokenUsage(10, 4, 0.1))


def test_designs_check_without_candidate_source() -> None:
    provider = Provider(
        json.dumps(
            {
                "id": "edge-case",
                "command": "python /work/checks/check.py",
                "files": [
                    {
                        "path": "check.py",
                        "content_b64": base64.b64encode(b"assert True\n").decode(),
                    }
                ],
            }
        )
    )
    designed = IndependentTestDesigner(provider).design("fix edge case", ("source.py",), 5)
    assert designed.check.files[0].content == b"assert True\n"
    assert designed.usage.input_tokens == 10
    prompt = json.dumps(provider.messages)
    assert "candidate" not in prompt.lower() or "do not see candidate" in prompt.lower()


@pytest.mark.parametrize(
    "response",
    ["not json", "[]", "{}", '{"id":"x","command":"true","files":[]}'],
)
def test_invalid_designer_output_fails_closed(response: str) -> None:
    provider: ProviderProtocol = Provider(response)
    with pytest.raises(ProviderError, match="invalid check"):
        IndependentTestDesigner(provider).design("task", (), 5)


def test_invalid_base64_fails_closed() -> None:
    response = json.dumps(
        {
            "id": "check",
            "command": "true",
            "files": [{"path": "x", "content_b64": "!!!"}],
        }
    )
    with pytest.raises(ProviderError):
        IndependentTestDesigner(Provider(response)).design("task", (), 5)
