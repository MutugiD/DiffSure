"""Docker-backed execution of untrusted repositories and derived checks."""

from __future__ import annotations

import io
import math
import subprocess
import tarfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from diffsure.verification import CheckOutcome, CheckResult, CheckSpec, DerivedFile

RunProcess = Callable[..., subprocess.CompletedProcess[bytes]]


class SandboxError(RuntimeError):
    """Raised before candidate execution when the sandbox cannot be prepared."""


class DockerSandbox:
    def __init__(
        self,
        image: str,
        *,
        docker_binary: str = "docker",
        output_limit: int = 64_000,
        runner: RunProcess = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.image = image
        self.docker_binary = docker_binary
        self.output_limit = output_limit
        self._runner = runner
        self._clock = clock

    def run(self, repository: Path, check: CheckSpec, timeout: float) -> CheckResult:
        if timeout <= 0:
            raise ValueError("sandbox timeout must be positive")
        payload = _sandbox_archive(repository, check.files)
        command = self._command(check.command, timeout)
        started = self._clock()
        try:
            completed = self._runner(
                command,
                input=payload,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout + 5,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = _bounded_output(exc.stdout or b"", self.output_limit)
            return CheckResult(
                check.check_id,
                check.kind,
                CheckOutcome.TIMED_OUT,
                None,
                self._elapsed(started),
                output,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return CheckResult(
                check.check_id,
                check.kind,
                CheckOutcome.INFRASTRUCTURE_FAILED,
                None,
                self._elapsed(started),
                f"sandbox unavailable: {type(exc).__name__}",
            )

        output = _bounded_output(completed.stdout, self.output_limit)
        if completed.returncode == 0:
            outcome = CheckOutcome.PASSED
        elif completed.returncode in {124, 137}:
            outcome = CheckOutcome.TIMED_OUT
        else:
            outcome = _classify_exit(output)
        return CheckResult(
            check.check_id,
            check.kind,
            outcome,
            completed.returncode,
            self._elapsed(started),
            output,
        )

    def _command(self, check_command: str, timeout: float) -> list[str]:
        script = (
            "set -eu; tar -xzf - -C /work; cd /work/repo; "
            'exec timeout --signal=KILL "$DIFFSURE_CHECK_TIMEOUT" sh -c "$1"'
        )
        return [
            self.docker_binary,
            "run",
            "--rm",
            "--interactive",
            "--network",
            "none",
            "--read-only",
            "--user",
            "65534:65534",
            "--cpus",
            "2",
            "--memory",
            "1g",
            "--pids-limit",
            "512",
            "--stop-timeout",
            "1",
            "--tmpfs",
            "/work:rw,exec,nosuid,nodev,size=512m,mode=1777",
            "--tmpfs",
            "/tmp:rw,exec,nosuid,nodev,size=128m,mode=1777",
            "--env",
            "HOME=/tmp",
            "--env",
            f"DIFFSURE_CHECK_TIMEOUT={math.ceil(timeout)}",
            self.image,
            "bash",
            "-c",
            script,
            "diffsure-check",
            check_command,
        ]

    def _elapsed(self, started: float) -> float:
        return round(max(0.0, self._clock() - started), 6)


def _sandbox_archive(repository: Path, files: Sequence[DerivedFile]) -> bytes:
    if not repository.is_dir():
        raise SandboxError("repository workspace is unavailable")
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz", dereference=False) as archive:
        for path in sorted(repository.rglob("*")):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise SandboxError("repository contains an unsupported entry")
            relative = path.relative_to(repository).as_posix()
            archive.add(path, arcname=f"repo/{relative}", recursive=False)
        for derived in files:
            info = tarfile.TarInfo(f"checks/{derived.path}")
            info.size = len(derived.content)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(derived.content))
    return output.getvalue()


def _bounded_output(raw: bytes, limit: int) -> str:
    if len(raw) > limit:
        raw = raw[:limit] + b"\n[output truncated]"
    return raw.decode("utf-8", errors="replace")


def _classify_exit(output: str) -> CheckOutcome:
    infrastructure_markers = (
        "unable to find image",
        "cannot connect to the docker daemon",
        "error response from daemon",
        "permission denied while trying to connect",
    )
    if any(marker in output.lower() for marker in infrastructure_markers):
        return CheckOutcome.INFRASTRUCTURE_FAILED
    return CheckOutcome.CANDIDATE_FAILED
