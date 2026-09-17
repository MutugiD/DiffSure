"""OpenAI Responses adapter with explicit no-storage policy."""

from __future__ import annotations

import json

from diffsure.providers.base import ModelTurn, ProviderError, TokenUsage, ToolCall
from diffsure.providers.http import post_json

TERRA_INPUT_PER_MILLION = 2.0
TERRA_OUTPUT_PER_MILLION = 12.0


class OpenAIProvider:
    name = "openai"

    def __init__(self, url: str, model: str, api_key: str) -> None:
        if not api_key:
            raise ProviderError("OpenAI API key is unavailable")
        self.url = url.rstrip("/")
        self.model = model
        self._api_key = api_key

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn:
        payload: dict[str, object] = {
            "model": self.model,
            "input": messages,
            "tools": tools,
            "store": False,
        }
        value = post_json(
            f"{self.url}/responses",
            payload,
            timeout,
            {"Authorization": f"Bearer {self._api_key}"},
        )
        output = value.get("output")
        if not isinstance(output, list):
            raise ProviderError("OpenAI response lacks output items")
        texts: list[str] = []
        calls: list[ToolCall] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "function_call":
                name = item.get("name")
                call_id = item.get("call_id") or item.get("id")
                arguments = item.get("arguments", "{}")
                if not isinstance(name, str) or not isinstance(call_id, str):
                    raise ProviderError("OpenAI function call is invalid")
                try:
                    decoded = json.loads(arguments) if isinstance(arguments, str) else arguments
                except json.JSONDecodeError as exc:
                    raise ProviderError("OpenAI function arguments are invalid") from exc
                if not isinstance(decoded, dict):
                    raise ProviderError("OpenAI function arguments must be an object")
                calls.append(ToolCall(call_id, name, decoded))
            if item.get("type") == "message":
                content = item.get("content", [])
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "output_text":
                            text = part.get("text")
                            if isinstance(text, str):
                                texts.append(text)
        raw_usage = value.get("usage")
        usage_dict = raw_usage if isinstance(raw_usage, dict) else {}
        input_tokens = _nonnegative_int(usage_dict.get("input_tokens"))
        output_tokens = _nonnegative_int(usage_dict.get("output_tokens"))
        cost = round(
            input_tokens * TERRA_INPUT_PER_MILLION / 1_000_000
            + output_tokens * TERRA_OUTPUT_PER_MILLION / 1_000_000,
            8,
        )
        return ModelTurn(
            "\n".join(texts), tuple(calls), TokenUsage(input_tokens, output_tokens, cost)
        )


def _nonnegative_int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
