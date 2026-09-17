"""Normalized model provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """Sanitized provider protocol or transport failure."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, object]


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            round(self.estimated_cost_usd + other.estimated_cost_usd, 8),
        )


@dataclass(frozen=True, slots=True)
class ModelTurn:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    usage: TokenUsage = TokenUsage()


class Provider(Protocol):
    name: str
    model: str

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn: ...
