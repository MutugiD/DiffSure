"""Git and public diff validation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

MAX_DIFF_BYTES = 200_000
FORBIDDEN_PREFIXES = (".git/", "acceptance/", "acceptance_tests/")


def static_diff_error(diff: bytes) -> str | None:
    if not diff:
        return "empty diff"
    if len(diff) > MAX_DIFF_BYTES:
        return "diff exceeds 200000 bytes"
    try:
        text = diff.decode("utf-8")
    except UnicodeDecodeError:
        return "diff is not valid UTF-8"
    if "\r" in text:
        return "diff does not use LF-only line endings"
    if not text.startswith("diff --git "):
        return "diff is not a Git unified diff"
    if "GIT binary patch" in text:
        return "binary patch content"
    if "new file mode 120000" in text or "new mode 120000" in text:
        return "symlink creation is not allowed"
    for line in text.splitlines():
        match = re.match(r"^diff --git a/(\S+) b/(\S+)$", line)
        if match is None:
            continue
        for value in match.groups():
            parts = value.split("/")
            if value.startswith("/") or ".." in parts:
                return f"path escapes repository: {value}"
            if value.startswith(FORBIDDEN_PREFIXES):
                return f"path is restricted: {value}"
    return None


def apply_check(repo: Path, diff: bytes, timeout: float) -> str | None:
    try:
        result = subprocess.run(
            ["git", "apply", "--check", "-"],
            cwd=repo,
            input=diff,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"git apply check failed: {type(exc).__name__}"
    if result.returncode == 0:
        return None
    return "diff does not apply cleanly: " + result.stderr.decode(errors="replace")[:500]


def apply_diff(repo: Path, diff: bytes, timeout: float) -> str | None:
    error = apply_check(repo, diff, timeout)
    if error is not None:
        return error
    try:
        result = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            cwd=repo,
            input=diff,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"git apply failed: {type(exc).__name__}"
    if result.returncode == 0:
        return None
    return "diff application failed: " + result.stderr.decode(errors="replace")[:500]
