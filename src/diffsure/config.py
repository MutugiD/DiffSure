"""Typed environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when environment configuration is invalid."""


def _integer(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}")
    return value


def _boolean(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, str(default)).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean")


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    provider: str
    model: str
    provider_url: str
    acceptance_image: str
    capacity: int
    health_skip_external: bool

    @classmethod
    def from_env(cls) -> Settings:
        provider = os.environ.get("DIFFSURE_PROVIDER", "ollama").strip().lower()
        if provider not in {"ollama", "openai"}:
            raise ConfigurationError("DIFFSURE_PROVIDER must be ollama or openai")
        model_default = "qwen3:8b" if provider == "ollama" else "gpt-5.6-terra"
        url_default = (
            "http://127.0.0.1:11434" if provider == "ollama" else "https://api.openai.com/v1"
        )
        return cls(
            host=os.environ.get("DIFFSURE_HOST", "0.0.0.0"),
            port=_integer("DIFFSURE_PORT", 8000, 1, 65535),
            provider=provider,
            model=os.environ.get("DIFFSURE_MODEL", model_default),
            provider_url=os.environ.get("DIFFSURE_PROVIDER_URL", url_default).rstrip("/"),
            acceptance_image=os.environ.get("DIFFSURE_ACCEPTANCE_IMAGE", "acceptance:latest"),
            capacity=_integer("DIFFSURE_CAPACITY", 3, 1, 64),
            health_skip_external=_boolean("DIFFSURE_HEALTH_SKIP_EXTERNAL"),
        )
