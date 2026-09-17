"""Create the explicitly configured provider without fallback."""

from __future__ import annotations

import os

from diffsure.config import Settings
from diffsure.providers import OllamaProvider, OpenAIProvider, Provider


def create_provider(settings: Settings) -> Provider:
    if settings.provider == "openai":
        return OpenAIProvider(
            settings.provider_url, settings.model, os.environ.get("OPENAI_API_KEY", "")
        )
    return OllamaProvider(settings.provider_url, settings.model)
