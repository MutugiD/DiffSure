"""Ollama chat adapter."""

from __future__ import annotations

from diffsure.providers.base import ModelTurn, ProviderError, TokenUsage, ToolCall
from diffsure.providers.http import post_json


class OllamaProvider:
    name = "ollama"

    def __init__(self, url: str, model: str) -> None:
        self.url = url.rstrip("/")
        self.model = model

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "think": False,
        }
        value = post_json(f"{self.url}/api/chat", payload, timeout)
        message = value.get("message")
        if not isinstance(message, dict):
            raise ProviderError("Ollama response lacks a message")
        text = message.get("content", "")
        if not isinstance(text, str):
            raise ProviderError("Ollama message content is invalid")
        calls: list[ToolCall] = []
        raw_calls = message.get("tool_calls", [])
        if not isinstance(raw_calls, list):
            raise ProviderError("Ollama tool calls are invalid")
        for index, raw in enumerate(raw_calls):
            if not isinstance(raw, dict) or not isinstance(raw.get("function"), dict):
                raise ProviderError("Ollama tool call is invalid")
            function = raw["function"]
            name = function.get("name")
            arguments = function.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise ProviderError("Ollama tool function is invalid")
            calls.append(ToolCall(f"ollama-{index}", name, arguments))
        usage = TokenUsage(
            input_tokens=_nonnegative_int(value.get("prompt_eval_count")),
            output_tokens=_nonnegative_int(value.get("eval_count")),
        )
        return ModelTurn(text, tuple(calls), usage)


def _nonnegative_int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
