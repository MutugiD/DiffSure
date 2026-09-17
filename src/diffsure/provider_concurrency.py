"""Provider-level concurrency independent of solve capacity."""

from __future__ import annotations

import threading
import time

from diffsure.providers import ModelTurn, Provider


class ConcurrentProvider:
    def __init__(self, provider: Provider, capacity: int) -> None:
        self._provider = provider
        self._semaphore = threading.BoundedSemaphore(capacity)
        self.name = provider.name
        self.model = provider.model

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn:
        started = time.monotonic()
        if timeout <= 0 or not self._semaphore.acquire(timeout=timeout):
            raise TimeoutError("provider queue deadline reached")
        try:
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError("provider queue deadline reached")
            return self._provider.complete(messages, tools, remaining)
        finally:
            self._semaphore.release()
