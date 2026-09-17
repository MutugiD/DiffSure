from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from diffsure.config import Settings
from diffsure.domain import SolveResponse, Usage
from diffsure.health import Health
from diffsure.server import DiffSureServer, create_server


class Ready:
    def inspect(self) -> Health:
        return Health(True, "fake", "fixture", "image", 3, {"provider": True})


class ConcurrentSolver:
    def __init__(self, block: bool = False) -> None:
        self.block = block
        self.entered = 0
        self.lock = threading.Lock()
        self.all_entered = threading.Event()
        self.release = threading.Event()

    def solve(self, payload: object) -> SolveResponse:
        assert isinstance(payload, dict)
        request_id = payload.get("request_id")
        assert isinstance(request_id, str)
        with self.lock:
            self.entered += 1
            if self.entered == 3:
                self.all_entered.set()
        if self.block:
            self.release.wait(timeout=3)
        if payload.get("fail"):
            raise RuntimeError("isolated fault")
        return SolveResponse(request_id, None, (), Usage("fake", "fixture"))


@contextmanager
def running(solver: ConcurrentSolver) -> Iterator[tuple[str, DiffSureServer]]:
    settings = Settings("127.0.0.1", 0, "ollama", "model", "url", "image", 3, True)
    server = create_server(settings, Ready(), solver)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", server
    finally:
        solver.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def post(url: str, request_id: str, fail: bool = False) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        f"{url}/solve",
        data=json.dumps({"request_id": request_id, "fail": fail}).encode(),
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_three_http_solves_are_isolated_and_health_reflects_capacity() -> None:
    solver = ConcurrentSolver(block=True)
    with running(solver) as (url, server), ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(post, url, f"request-{index}") for index in range(3)]
        assert solver.all_entered.wait(timeout=3)
        try:
            urllib.request.urlopen(f"{url}/health", timeout=2)
        except urllib.error.HTTPError as raised:
            assert raised.code == 503
            assert json.load(raised)["capacity"] == 0
        solver.release.set()
        responses = [future.result(timeout=3) for future in futures]
        assert {value[1]["request_id"] for value in responses} == {
            "request-0",
            "request-1",
            "request-2",
        }
        assert all(status == 200 for status, _value in responses)
        counters = server.metrics.snapshot()["counters"]
        assert isinstance(counters, dict)
        assert counters["requests"] == 3


def test_one_fault_does_not_contaminate_other_requests() -> None:
    solver = ConcurrentSolver()
    with running(solver) as (url, _server), ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(post, url, "good-1"),
            pool.submit(post, url, "bad", True),
            pool.submit(post, url, "good-2"),
        ]
        responses = [future.result(timeout=3) for future in futures]
    assert sorted(status for status, _value in responses) == [200, 200, 500]
    bodies = [value for status, value in responses if status == 200]
    assert {value["request_id"] for value in bodies} == {"good-1", "good-2"}
