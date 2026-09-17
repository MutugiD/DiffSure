"""Dependency readiness checks with sanitized output."""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from diffsure.config import Settings
from diffsure.domain import CONTRACT_VERSION
from diffsure.operations import CapacityManager


@dataclass(frozen=True, slots=True)
class Health:
    ready: bool
    provider: str
    model: str
    sandbox_image: str
    capacity: int
    checks: dict[str, bool]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "provider": self.provider,
            "model": self.model,
            "sandbox_image": self.sandbox_image,
            "capacity": self.capacity,
            "checks": self.checks,
            "contract_version": CONTRACT_VERSION,
        }


class Probe(Protocol):
    def inspect(self) -> Health: ...


class DependencyProbe:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def inspect(self) -> Health:
        if self.settings.health_skip_external:
            checks = {"git": True, "docker": True, "acceptance_image": True, "provider": True}
        else:
            checks = {
                "git": shutil.which("git") is not None,
                "docker": self._docker_ready(),
                "acceptance_image": self._image_ready(),
                "provider": self._provider_ready(),
            }
        return Health(
            ready=all(checks.values()),
            provider=self.settings.provider,
            model=self.settings.model,
            sandbox_image=self.settings.acceptance_image,
            capacity=self.settings.capacity,
            checks=checks,
        )

    @staticmethod
    def _docker_ready() -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _image_ready(self) -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.settings.acceptance_image],
                capture_output=True,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _provider_ready(self) -> bool:
        if self.settings.provider == "openai":
            return bool(os.environ.get("OPENAI_API_KEY"))
        request = urllib.request.Request(f"{self.settings.provider_url}/api/tags")
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return bool(response.status == 200)
        except (OSError, urllib.error.URLError):
            return False


class CapacityProbe:
    def __init__(self, probe: Probe, capacity: CapacityManager) -> None:
        self.probe = probe
        self.capacity = capacity

    def inspect(self) -> Health:
        health = self.probe.inspect()
        available = self.capacity.available
        checks = {**health.checks, "capacity": available > 0}
        return Health(
            ready=health.ready and available > 0,
            provider=health.provider,
            model=health.model,
            sandbox_image=health.sandbox_image,
            capacity=available,
            checks=checks,
        )
