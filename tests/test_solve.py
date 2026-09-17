from __future__ import annotations

import base64
import io
import json
import subprocess
import tarfile
from pathlib import Path

from diffsure.config import Settings
from diffsure.providers import ModelTurn, ProviderError, TokenUsage, ToolCall
from diffsure.solve import VerifiedPatchSolver
from diffsure.verification import CheckOutcome, CheckResult, CheckSpec

PATCH = """diff --git a/source.py b/source.py
index 63566d8..7a5e7c3 100644
--- a/source.py
+++ b/source.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""


class ScriptedProvider:
    name = "fake"
    model = "fixture"

    def __init__(self, *, patch: bool = True, invalid_design: bool = False) -> None:
        self.calls = 0
        self.patch = patch
        self.invalid_design = invalid_design

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        timeout: float,
    ) -> ModelTurn:
        self.calls += 1
        if self.calls == 1:
            if self.invalid_design:
                return ModelTurn("not json")
            check = {
                "id": "value-check",
                "command": "python3 /work/checks/check.py",
                "files": [
                    {
                        "path": "check.py",
                        "content_b64": base64.b64encode(
                            b"from pathlib import Path\n"
                            b"assert 'VALUE = 2' in "
                            b"Path('/work/repo/source.py').read_text()\n"
                        ).decode(),
                    }
                ],
            }
            return ModelTurn(json.dumps(check), usage=TokenUsage(4, 2, 0.0))
        if self.calls == 2 and self.patch:
            return ModelTurn(tool_calls=(ToolCall("patch", "apply_patch", {"diff": PATCH}),))
        if self.calls == 3 and self.patch:
            return ModelTurn(tool_calls=(ToolCall("diff", "git_diff", {}),))
        return ModelTurn("done", usage=TokenUsage(3, 1, 0.0))


class ObservingSandbox:
    def __init__(self, *, fail_delivery: bool = False) -> None:
        self.calls = 0
        self.fail_delivery = fail_delivery

    def run(self, repository: Path, check: CheckSpec, timeout: float) -> CheckResult:
        self.calls += 1
        changed = (repository / "source.py").read_text(encoding="utf-8") == "VALUE = 2\n"
        delivery_failure = self.fail_delivery and self.calls >= 4
        baseline_failure = self.calls == 1
        outcome = (
            CheckOutcome.PASSED
            if changed and not delivery_failure and not baseline_failure
            else CheckOutcome.CANDIDATE_FAILED
        )
        return CheckResult(check.check_id, check.kind, outcome, 0, 0.01, "observed")


def settings() -> Settings:
    return Settings("127.0.0.1", 0, "ollama", "model", "url", "acceptance:latest", 3, True)


def repository_archive(tmp_path: Path) -> str:
    repo = tmp_path / "input"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "source.py").write_bytes(b"VALUE = 1\n")
    (repo / "run_tests.sh").write_bytes(b"grep -q 'VALUE = 2' source.py\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        archive.add(repo, arcname="repo")
    return base64.b64encode(output.getvalue()).decode()


def payload(archive: str, deadline: float = 120) -> dict[str, object]:
    return {
        "request_id": "solve-1",
        "repo_archive_b64": archive,
        "task": "change VALUE from 1 to 2",
        "deadline_seconds": deadline,
    }


def test_returns_diff_only_after_candidate_and_clean_delivery_pass(tmp_path: Path) -> None:
    sandbox = ObservingSandbox()
    response = VerifiedPatchSolver(settings(), ScriptedProvider(), sandbox).solve(
        payload(repository_archive(tmp_path))
    )
    assert response.diff is not None
    assert "-VALUE = 1\n+VALUE = 2\n" in response.diff
    assert sandbox.calls == 5
    assert response.usage.input_tokens == 7
    phases = [item.get("phase") for item in response.record if "phase" in item]
    assert phases == [
        "baseline",
        "test_design",
        "static_gate",
        "candidate_gate",
        "delivery_gate",
    ]


def test_fails_closed_when_no_diff_is_produced(tmp_path: Path) -> None:
    response = VerifiedPatchSolver(
        settings(), ScriptedProvider(patch=False), ObservingSandbox()
    ).solve(payload(repository_archive(tmp_path)))
    assert response.diff is None
    assert any(item.get("phase") == "static_gate" for item in response.record)


def test_fails_closed_when_delivery_copy_fails(tmp_path: Path) -> None:
    response = VerifiedPatchSolver(
        settings(), ScriptedProvider(), ObservingSandbox(fail_delivery=True)
    ).solve(payload(repository_archive(tmp_path)))
    assert response.diff is None
    assert response.record[-1]["phase"] == "delivery_gate"


def test_provider_failure_is_audited_as_null(tmp_path: Path) -> None:
    response = VerifiedPatchSolver(
        settings(), ScriptedProvider(invalid_design=True), ObservingSandbox()
    ).solve(payload(repository_archive(tmp_path)))
    assert response.diff is None
    assert response.record[-1]["reason"] == ProviderError.__name__


def test_short_deadline_fails_closed_without_provider_call(tmp_path: Path) -> None:
    provider = ScriptedProvider()
    response = VerifiedPatchSolver(settings(), provider, ObservingSandbox()).solve(
        payload(repository_archive(tmp_path), 1)
    )
    assert response.diff is None
    assert provider.calls == 0
    assert response.record[-1]["reason"] == "deadline_too_short"
