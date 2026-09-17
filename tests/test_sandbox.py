from __future__ import annotations

import subprocess
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from diffsure.sandbox import DockerSandbox, SandboxError
from diffsure.verification import CheckKind, CheckOutcome, CheckSpec, DerivedFile


def repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "run_tests.sh").write_text("exit 0\n", encoding="utf-8")
    return repo


def test_runs_with_hardened_docker_controls_and_separate_checks(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured.update(command=command, **kwargs)
        return subprocess.CompletedProcess(command, 0, b"passed\n")

    check = CheckSpec(
        "task-check",
        CheckKind.DERIVED,
        "python /work/checks/check.py",
        (DerivedFile("check.py", b"print('ok')\n"),),
    )
    result = DockerSandbox("acceptance:test", runner=runner).run(repository(tmp_path), check, 9)

    command = captured["command"]
    assert isinstance(command, list)
    for expected in ("none", "--read-only", "65534:65534", "2", "1g", "512"):
        assert expected in command
    assert command[-1] == check.command
    assert captured["timeout"] == 14
    input_value = captured["input"]
    assert isinstance(input_value, bytes)
    with tarfile.open(fileobj=BytesIO(input_value), mode="r:gz") as archive:
        assert set(archive.getnames()) == {"repo/run_tests.sh", "checks/check.py"}
    assert result.passed


def test_candidate_failure_is_distinct_from_infrastructure_failure(tmp_path: Path) -> None:
    def candidate(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 1, b"assertion failed")

    def infrastructure(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 125, b"Cannot connect to the Docker daemon")

    check = CheckSpec.repository_suite()
    repo = repository(tmp_path)
    assert (
        DockerSandbox("image", runner=candidate).run(repo, check, 2).outcome
        is CheckOutcome.CANDIDATE_FAILED
    )
    assert (
        DockerSandbox("image", runner=infrastructure).run(repo, check, 2).outcome
        is CheckOutcome.INFRASTRUCTURE_FAILED
    )


def test_timeout_and_missing_runtime_are_observed(tmp_path: Path) -> None:
    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired("docker", 1, output=b"partial")

    def missing(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError

    check = CheckSpec.repository_suite()
    repo = repository(tmp_path)
    timed = DockerSandbox("image", runner=timeout).run(repo, check, 1)
    failed = DockerSandbox("image", runner=missing).run(repo, check, 1)
    assert timed.outcome is CheckOutcome.TIMED_OUT
    assert timed.output == "partial"
    assert failed.outcome is CheckOutcome.INFRASTRUCTURE_FAILED


def test_output_is_bounded(tmp_path: Path) -> None:
    def noisy(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 1, b"x" * 100)

    result = DockerSandbox("image", runner=noisy, output_limit=10).run(
        repository(tmp_path), CheckSpec.repository_suite(), 1
    )
    assert result.output.endswith("[output truncated]")


def test_rejects_symlinks_before_docker(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    try:
        (repo / "link").symlink_to(repo / "run_tests.sh")
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(SandboxError):
        DockerSandbox("image").run(repo, CheckSpec.repository_suite(), 1)


def test_requires_positive_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        DockerSandbox("image").run(repository(tmp_path), CheckSpec.repository_suite(), 0)
