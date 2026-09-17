"""Standard-library HTTP boundary."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from diffsure.config import Settings
from diffsure.health import DependencyProbe, Probe


class DiffSureServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], probe: Probe) -> None:
        self.probe = probe
        super().__init__(address, RequestHandler)


class RequestHandler(BaseHTTPRequestHandler):
    server: DiffSureServer
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        health = self.server.probe.inspect()
        status = HTTPStatus.OK if health.ready else HTTPStatus.SERVICE_UNAVAILABLE
        self._json(status, health.as_dict())

    def do_POST(self) -> None:
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: HTTPStatus, body: dict[str, object]) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def create_server(settings: Settings, probe: Probe | None = None) -> DiffSureServer:
    return DiffSureServer((settings.host, settings.port), probe or DependencyProbe(settings))
