from __future__ import annotations

from pathlib import Path

from diffsure.agent import run_agent
from diffsure.providers import ModelTurn, TokenUsage, ToolCall
from diffsure.tools import RepositoryTools


class FakeProvider:
    name = "fake"
    model = "fixture"

    def __init__(self) -> None:
        self.turn = 0

    def complete(self, messages, tools, timeout):  # type: ignore[no-untyped-def]
        self.turn += 1
        if self.turn == 1:
            return ModelTurn(
                "inspect",
                (ToolCall("call-1", "list_files", {}),),
                TokenUsage(2, 1, 0.1),
            )
        return ModelTurn("done", usage=TokenUsage(3, 2, 0.2))


def test_agent_records_ordered_tool_loop(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello")
    result = run_agent(FakeProvider(), RepositoryTools(tmp_path), "fix", 5)
    assert result.text == "done"
    assert [item.get("type", "tool") for item in result.record] == [
        "text",
        "tool_call",
        "tool",
        "text",
    ]
    assert result.usage.input_tokens == 5
    assert result.usage.estimated_cost_usd == 0.3
    assert result.turns == 2


def test_agent_stops_at_turn_limit(tmp_path: Path) -> None:
    class Endless(FakeProvider):
        def complete(self, messages, tools, timeout):  # type: ignore[no-untyped-def]
            return ModelTurn(tool_calls=(ToolCall("call", "list_files", {}),))

    result = run_agent(Endless(), RepositoryTools(tmp_path), "fix", 1, max_turns=2)
    assert result.turns == 2
