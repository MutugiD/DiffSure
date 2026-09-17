from __future__ import annotations

import os
from pathlib import Path

import pytest

from diffsure.sandbox import DockerSandbox
from diffsure.verification import CheckSpec

pytestmark = pytest.mark.docker


STACK_COMMANDS = {
    "python": "python3 -c \"print('ok')\"",
    "javascript": "node -e \"console.log('ok')\"",
    "bash": 'bash -c "echo ok"',
    "go": "go version",
    "c": "printf 'int main(void){return 0;}' | gcc -x c - -o /tmp/check && /tmp/check",
    "rust": "printf 'fn main(){}' | rustc - -o /tmp/check && /tmp/check",
    "java": "java -version",
}


@pytest.mark.skipif(
    os.environ.get("DIFFSURE_DOCKER_TEST") != "1", reason="Docker integration is opt-in"
)
@pytest.mark.parametrize("stack", tuple(STACK_COMMANDS))
def test_acceptance_image_supports_stack(tmp_path: Path, stack: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "run_tests.sh").write_bytes(
        f"#!/usr/bin/env bash\nset -eu\n{STACK_COMMANDS[stack]}\n".encode()
    )
    result = DockerSandbox("acceptance:latest").run(repo, CheckSpec.repository_suite(), 30)
    assert result.passed, result.output
