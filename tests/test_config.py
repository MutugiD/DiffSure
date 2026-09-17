from __future__ import annotations

import pytest

from diffsure.config import ConfigurationError, Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DIFFSURE_PROVIDER",
        "DIFFSURE_MODEL",
        "DIFFSURE_PROVIDER_URL",
        "DIFFSURE_PORT",
        "DIFFSURE_CAPACITY",
        "DIFFSURE_PROVIDER_CAPACITY",
        "DIFFSURE_HEALTH_SKIP_EXTERNAL",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings.from_env()
    assert settings.provider == "ollama"
    assert settings.model == "qwen3:8b"
    assert settings.port == 8000
    assert settings.capacity == 3
    assert settings.provider_capacity == 1
    assert not settings.health_skip_external


def test_openai_defaults_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIFFSURE_PROVIDER", "openai")
    monkeypatch.setenv("DIFFSURE_MODEL", "example-model")
    monkeypatch.setenv("DIFFSURE_PROVIDER_URL", "https://example.test/v1/")
    monkeypatch.setenv("DIFFSURE_PORT", "9000")
    monkeypatch.setenv("DIFFSURE_CAPACITY", "5")
    monkeypatch.setenv("DIFFSURE_PROVIDER_CAPACITY", "2")
    monkeypatch.setenv("DIFFSURE_HEALTH_SKIP_EXTERNAL", "yes")
    settings = Settings.from_env()
    assert settings.model == "example-model"
    assert settings.provider_url == "https://example.test/v1"
    assert settings.port == 9000
    assert settings.capacity == 5
    assert settings.provider_capacity == 2
    assert settings.health_skip_external


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DIFFSURE_PROVIDER", "unknown"),
        ("DIFFSURE_PORT", "zero"),
        ("DIFFSURE_PORT", "0"),
        ("DIFFSURE_CAPACITY", "65"),
        ("DIFFSURE_PROVIDER_CAPACITY", "0"),
        ("DIFFSURE_HEALTH_SKIP_EXTERNAL", "perhaps"),
    ],
)
def test_invalid_configuration(monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError):
        Settings.from_env()
