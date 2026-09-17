from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from diffsure.config import Settings
from diffsure.health import Health
from diffsure.server import DiffSureServer, create_server


class StaticProbe:
    def __init__(self, ready: bool) -> None:
        self.ready = ready

    def inspect(self) -> Health:
        return Health(self.ready, "ollama", "model", "image", 3, {"git": self.ready})


@contextmanager
def running(ready: bool) -> Iterator[str]:
    settings = Settings("127.0.0.1", 0, "ollama", "model", "url", "image", 3, False)
    server = create_server(settings, StaticProbe(ready))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_health_ready() -> None:
    with running(True) as url, urllib.request.urlopen(f"{url}/health") as response:
        assert response.status == 200
        assert json.load(response)["status"] == "ready"


def test_health_not_ready() -> None:
    with running(False) as url:
        with pytest.raises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(f"{url}/health")
        assert raised.value.code == 503


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_unknown_route(method: str) -> None:
    with running(True) as url:
        request = urllib.request.Request(f"{url}/missing", method=method)
        with pytest.raises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request)
        assert raised.value.code == 404


def test_server_properties() -> None:
    assert DiffSureServer.daemon_threads
    assert DiffSureServer.allow_reuse_address
