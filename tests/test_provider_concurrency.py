from __future__ import annotations

import threading
import time

import pytest

from diffsure.provider_concurrency import ConcurrentProvider
from diffsure.providers import ModelTurn


class BlockingProvider:
    name = "ollama"
    model = "fixture"

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def complete(self, messages, tools, timeout):  # type: ignore[no-untyped-def]
        self.entered.set()
        self.release.wait(timeout=2)
        return ModelTurn("done")


def test_provider_queue_honors_its_deadline() -> None:
    provider = BlockingProvider()
    queued = ConcurrentProvider(provider, 1)
    thread = threading.Thread(target=lambda: queued.complete([], [], 2))
    thread.start()
    assert provider.entered.wait(timeout=1)
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        queued.complete([], [], 0.05)
    assert time.monotonic() - started < 0.5
    provider.release.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
