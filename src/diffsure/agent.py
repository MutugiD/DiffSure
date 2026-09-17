"""Provider-neutral bounded repository tool loop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from diffsure.providers import ModelTurn, Provider, TokenUsage
from diffsure.tools import RepositoryTools


@dataclass(frozen=True, slots=True)
class AgentResult:
    text: str
    record: tuple[dict[str, object], ...]
    usage: TokenUsage
    turns: int


def run_agent(
    provider: Provider,
    tools: RepositoryTools,
    instructions: str,
    timeout: float,
    max_turns: int = 12,
    remaining: Callable[[], float] | None = None,
) -> AgentResult:
    messages: list[dict[str, object]] = [{"role": "user", "content": instructions}]
    record: list[dict[str, object]] = []
    usage = TokenUsage()
    final_text = ""
    for turn_number in range(1, max_turns + 1):
        turn_timeout = timeout if remaining is None else min(timeout, remaining())
        if turn_timeout <= 0:
            return AgentResult(final_text, tuple(record), usage, turn_number - 1)
        turn = provider.complete(messages, tools.definitions(), turn_timeout)
        usage += turn.usage
        if turn.text:
            final_text = turn.text
            record.append({"role": "assistant", "type": "text", "text": turn.text})
        if not turn.tool_calls:
            return AgentResult(final_text, tuple(record), usage, turn_number)
        messages.append(_assistant_message(turn))
        for call in turn.tool_calls:
            record.append(
                {
                    "role": "assistant",
                    "type": "tool_call",
                    "name": call.name,
                    "input": call.arguments,
                }
            )
            result = tools.dispatch(call.name, call.arguments)
            record.append(
                {
                    "role": "tool",
                    "name": call.name,
                    "output": result.output,
                    "is_error": result.is_error,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "name": call.name,
                    "content": result.output,
                }
            )
    return AgentResult(final_text, tuple(record), usage, max_turns)


def _assistant_message(turn: ModelTurn) -> dict[str, object]:
    return {
        "role": "assistant",
        "content": turn.text,
        "tool_calls": [
            {
                "id": call.call_id,
                "type": "function",
                "function": {"name": call.name, "arguments": call.arguments},
            }
            for call in turn.tool_calls
        ],
    }
