from __future__ import annotations

import json

from diffsure.cli import main
from diffsure.health import Health


def test_doctor_ready(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        "diffsure.cli.DependencyProbe.inspect",
        lambda _self: Health(True, "ollama", "model", "image", 3, {"git": True}),
    )
    assert main(["doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ready"


def test_doctor_not_ready(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        "diffsure.cli.DependencyProbe.inspect",
        lambda _self: Health(False, "ollama", "model", "image", 3, {"git": False}),
    )
    assert main(["doctor"]) == 3
