from __future__ import annotations

import subprocess
from pathlib import Path

from diffsure.tools import RepositoryTools


def repository(path: Path) -> RepositoryTools:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=path, check=True)
    (path / "source.txt").write_bytes(b"old value\n")
    (path / "binary.bin").write_bytes(b"\xff")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "base",
        ],
        cwd=path,
        check=True,
    )
    return RepositoryTools(path)


def test_repository_read_search_and_paths(tmp_path: Path) -> None:
    tools = repository(tmp_path)
    assert "source.txt" in tools.dispatch("list_files", {}).output
    assert tools.dispatch("read_file", {"path": "source.txt"}).output == "old value\n"
    assert "source.txt:1" in tools.dispatch("search_text", {"query": "old"}).output
    assert tools.dispatch("read_file", {"path": "../secret"}).is_error
    assert tools.dispatch("read_file", {"path": "missing"}).is_error
    assert tools.dispatch("search_text", {"query": ""}).is_error


def test_patch_and_diff(tmp_path: Path) -> None:
    tools = repository(tmp_path)
    diff = (
        "diff --git a/source.txt b/source.txt\n"
        "--- a/source.txt\n+++ b/source.txt\n@@ -1 +1 @@\n-old value\n+new value\n"
    )
    assert not tools.dispatch("apply_patch", {"diff": diff}).is_error
    assert "+new value" in tools.dispatch("git_diff", {}).output
    assert tools.dispatch("apply_patch", {"diff": "bad"}).is_error


def test_diff_includes_new_and_deleted_files(tmp_path: Path) -> None:
    tools = repository(tmp_path)
    (tmp_path / "source.txt").unlink()
    (tmp_path / "created.txt").write_bytes(b"created\n")
    diff = tools.dispatch("git_diff", {}).output
    assert "deleted file mode" in diff
    assert "new file mode" in diff
    assert "+created" in diff


def test_requests_and_unknown_tool(tmp_path: Path) -> None:
    tools = repository(tmp_path)
    assert not tools.dispatch("request_repository_tests", {}).is_error
    assert tools.test_requests == 1
    result = tools.dispatch(
        "submit_derived_check",
        {"path": "checks/test.py", "content": "assert True", "command": "python checks/test.py"},
    )
    assert not result.is_error
    assert tools.derived_checks[0]["path"] == "checks/test.py"
    assert tools.dispatch("unknown", {}).is_error


def test_definitions_and_bounded_output(tmp_path: Path) -> None:
    tools = repository(tmp_path)
    assert len(tools.definitions()) == 7
    (tmp_path / "large.txt").write_text("x" * 60_000)
    assert tools.dispatch("read_file", {"path": "large.txt"}).output.endswith("[truncated]")
