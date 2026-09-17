from __future__ import annotations

import subprocess
import urllib.error

import pytest

from diffsure.config import Settings
from diffsure.health import DependencyProbe, Health


def settings(**changes: object) -> Settings:
    values: dict[str, object] = {
        "host": "127.0.0.1",
        "port": 0,
        "provider": "ollama",
        "model": "qwen3:8b",
        "provider_url": "http://127.0.0.1:11434",
        "acceptance_image": "acceptance:latest",
        "capacity": 3,
        "health_skip_external": False,
    }
    values.update(changes)
    return Settings(**values)  # type: ignore[arg-type]


def test_health_serialization() -> None:
    health = Health(True, "ollama", "model", "image", 2, {"git": True})
    assert health.as_dict()["status"] == "ready"


def test_external_skip_is_ready() -> None:
    health = DependencyProbe(settings(health_skip_external=True)).inspect()
    assert health.ready
    assert all(health.checks.values())


def test_missing_tools_are_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("diffsure.health.shutil.which", lambda _name: None)
    monkeypatch.setattr(DependencyProbe, "_provider_ready", lambda _self: False)
    health = DependencyProbe(settings()).inspect()
    assert not health.ready
    assert health.checks == {"git": False, "docker": False, "provider": False}


def test_docker_probe_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("diffsure.health.shutil.which", lambda _name: "tool")
    result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess([], 0)
    monkeypatch.setattr("diffsure.health.subprocess.run", lambda *args, **kwargs: result)
    assert DependencyProbe._docker_ready()


def test_docker_probe_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("diffsure.health.shutil.which", lambda _name: "docker")

    def timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired("docker", 3)

    monkeypatch.setattr("diffsure.health.subprocess.run", timeout)
    assert not DependencyProbe._docker_ready()


def test_ollama_probe_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("diffsure.health.urllib.request.urlopen", fail)
    assert not DependencyProbe(settings())._provider_ready()


def test_openai_probe_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert not DependencyProbe(settings(provider="openai"))._provider_ready()
    monkeypatch.setenv("OPENAI_API_KEY", "present")
    assert DependencyProbe(settings(provider="openai"))._provider_ready()
