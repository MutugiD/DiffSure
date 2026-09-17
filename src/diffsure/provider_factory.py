"""Create the explicitly configured provider without fallback."""

from __future__ import annotations

import os

from diffsure.config import Settings
from diffsure.provider_concurrency import ConcurrentProvider
from diffsure.providers import OllamaProvider, OpenAIProvider, Provider


def create_provider(settings: Settings) -> Provider:
    if settings.provider == "openai":
        return ConcurrentProvider(
            OpenAIProvider(
                settings.provider_url, settings.model, os.environ.get("OPENAI_API_KEY", "")
            ),
            settings.provider_capacity,
        )
    return ConcurrentProvider(
        OllamaProvider(settings.provider_url, settings.model), settings.provider_capacity
    )
