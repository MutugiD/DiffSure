from __future__ import annotations

import io
import json
import urllib.error

import pytest

from diffsure.provider_concurrency import ConcurrentProvider
from diffsure.provider_factory import create_provider
from diffsure.providers import OllamaProvider, OpenAIProvider, ProviderError
from diffsure.providers.http import post_json
from tests.test_archive import settings


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def test_post_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "diffsure.providers.http.urllib.request.urlopen",
        lambda request, timeout: Response(b'{"ok":true}'),
    )
    assert post_json("https://example.test", {"value": 1}, 2) == {"ok": True}


def test_post_json_sanitizes_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("secret detail")

    monkeypatch.setattr("diffsure.providers.http.urllib.request.urlopen", fail)
    with pytest.raises(ProviderError, match="URLError"):
        post_json("https://example.test", {}, 2)


def test_ollama_normalizes_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "diffsure.providers.ollama.post_json",
        lambda *_args, **_kwargs: {
            "message": {
                "content": "inspect",
                "tool_calls": [{"function": {"name": "list_files", "arguments": {}}}],
            },
            "prompt_eval_count": 10,
            "eval_count": 4,
        },
    )
    turn = OllamaProvider("http://localhost:11434/", "model").complete([], [], 2)
    assert turn.text == "inspect"
    assert turn.tool_calls[0].name == "list_files"
    assert turn.usage.input_tokens == 10


@pytest.mark.parametrize(
    "value",
    [{}, {"message": []}, {"message": {"content": 1}}, {"message": {"tool_calls": {}}}],
)
def test_ollama_rejects_malformed_turn(
    monkeypatch: pytest.MonkeyPatch, value: dict[str, object]
) -> None:
    monkeypatch.setattr("diffsure.providers.ollama.post_json", lambda *_args, **_kwargs: value)
    with pytest.raises(ProviderError):
        OllamaProvider("url", "model").complete([], [], 1)


def test_openai_normalizes_turn_and_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "diffsure.providers.openai.post_json",
        lambda *_args, **_kwargs: {
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "done"}]},
                {
                    "type": "function_call",
                    "id": "call-1",
                    "name": "read_file",
                    "arguments": json.dumps({"path": "README.md"}),
                },
            ],
            "usage": {"input_tokens": 1_000_000, "output_tokens": 1_000_000},
        },
    )
    turn = OpenAIProvider("https://api.example/v1/", "gpt-5.6-terra", "key").complete([], [], 2)
    assert turn.text == "done"
    assert turn.tool_calls[0].arguments == {"path": "README.md"}
    assert turn.usage.estimated_cost_usd == 14.0


def test_openai_requires_key_and_valid_output(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ProviderError):
        OpenAIProvider("url", "model", "")
    monkeypatch.setattr("diffsure.providers.openai.post_json", lambda *_args, **_kwargs: {})
    with pytest.raises(ProviderError):
        OpenAIProvider("url", "model", "key").complete([], [], 1)


def test_provider_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    assert isinstance(create_provider(settings()), ConcurrentProvider)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    assert isinstance(create_provider(settings(provider="openai")), ConcurrentProvider)
