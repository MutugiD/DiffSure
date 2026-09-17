from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from diffsure.git import apply_check, static_diff_error

VALID = (
    b"diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new\n"
)


@pytest.mark.parametrize(
    ("diff", "reason"),
    [
        (b"", "empty"),
        (b"x" * 200_001, "exceeds"),
        (b"\xff", "UTF-8"),
        (VALID.replace(b"\n", b"\r\n"), "LF-only"),
        (b"not a diff", "unified"),
        (b"diff --git a/x b/x\nGIT binary patch\n", "binary"),
        (b"diff --git a/x b/x\nnew file mode 120000\n", "symlink"),
        (b"diff --git a/../x b/../x\n", "escapes"),
        (b"diff --git a/.git/x b/.git/x\n", "restricted"),
    ],
    ids=[
        "empty",
        "oversize",
        "encoding",
        "crlf",
        "format",
        "binary",
        "symlink",
        "escape",
        "restricted",
    ],
)
def test_static_diff_rejections(diff: bytes, reason: str) -> None:
    assert reason in (static_diff_error(diff) or "")


def test_valid_static_diff() -> None:
    assert static_diff_error(VALID) is None


def test_apply_check(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_bytes(b"old\n")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    assert apply_check(tmp_path, VALID, 2) is None
    assert "does not apply" in (apply_check(tmp_path, VALID.replace(b"old", b"missing"), 2) or "")


def test_apply_check_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git", 1)

    monkeypatch.setattr("diffsure.git.subprocess.run", timeout)
    assert "TimeoutExpired" in (apply_check(tmp_path, VALID, 1) or "")
