from __future__ import annotations

import json
import os
import threading
import urllib.request
from pathlib import Path

import pytest

from diffsure.health import Health
from diffsure.sandbox import DockerSandbox
from diffsure.server import create_server
from diffsure.solve import VerifiedPatchSolver
from tests.test_solve import ScriptedProvider, payload, repository_archive, settings

pytestmark = pytest.mark.docker


class ReadyProbe:
    def inspect(self) -> Health:
        return Health(True, "fake", "fixture", "acceptance:latest", 1, {"docker": True})


@pytest.mark.skipif(
    os.environ.get("DIFFSURE_DOCKER_TEST") != "1", reason="Docker integration is opt-in"
)
def test_http_request_returns_diff_after_clean_container_gate(tmp_path: Path) -> None:
    configured = settings()
    solver = VerifiedPatchSolver(configured, ScriptedProvider(), DockerSandbox("acceptance:latest"))
    server = create_server(configured, ReadyProbe(), solver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body = json.dumps(payload(repository_archive(tmp_path))).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_address[1]}/solve",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.load(response)
        assert response.status == 200
        assert "-VALUE = 1\n+VALUE = 2\n" in value["diff"]
        assert value["record"][-1]["phase"] == "delivery_gate"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
