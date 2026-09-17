"""Standard-library HTTP boundary."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from diffsure.config import Settings
from diffsure.domain import CONTRACT_VERSION, RequestError
from diffsure.health import CapacityProbe, DependencyProbe, Probe
from diffsure.operations import CapacityError, CapacityManager, ManagedSolver, OperationalMetrics
from diffsure.solve import IngestionSolver, Solver


class DiffSureServer(ThreadingHTTPServer):
    daemon_threads = False
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        probe: Probe,
        solver: Solver,
        max_request_bytes: int,
        capacity: CapacityManager,
        metrics: OperationalMetrics,
    ) -> None:
        self.probe = probe
        self.solver = solver
        self.max_request_bytes = max_request_bytes
        self.capacity = capacity
        self.metrics = metrics
        super().__init__(address, RequestHandler)

    def shutdown(self) -> None:
        self.capacity.close()
        super().shutdown()


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
        if self.path != "/solve":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except ValueError:
            self._json(HTTPStatus.LENGTH_REQUIRED, {"error": "content_length_required"})
            return
        if length <= 0 or length > self.server.max_request_bytes:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request_too_large"})
            return
        body = self.rfile.read(length)
        requested_contract = self.headers.get("X-DiffSure-Contract", CONTRACT_VERSION)
        if requested_contract != CONTRACT_VERSION:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "unsupported_contract_version"})
            return
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        try:
            response = self.server.solver.solve(payload)
        except CapacityError:
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "capacity_unavailable"})
            return
        except RequestError as exc:
            self._json(HTTPStatus(exc.status), {"error": str(exc)})
            return
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error"})
            return
        self._json(HTTPStatus.OK, response.as_dict())

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: HTTPStatus, body: dict[str, object]) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-DiffSure-Contract", CONTRACT_VERSION)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def create_server(
    settings: Settings, probe: Probe | None = None, solver: Solver | None = None
) -> DiffSureServer:
    capacity = CapacityManager(settings.capacity)
    metrics = OperationalMetrics()
    managed = ManagedSolver(solver or IngestionSolver(settings), capacity, metrics)
    return DiffSureServer(
        (settings.host, settings.port),
        CapacityProbe(probe or DependencyProbe(settings), capacity),
        managed,
        settings.max_request_bytes,
        capacity,
        metrics,
    )
