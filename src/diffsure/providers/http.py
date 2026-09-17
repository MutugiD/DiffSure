"""Small JSON HTTP helper shared by provider adapters."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from diffsure.providers.base import ProviderError


def post_json(
    url: str, payload: dict[str, object], timeout: float, headers: dict[str, str] | None = None
) -> dict[str, object]:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers=request_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider request failed: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ProviderError("provider returned a non-object response")
    return value
