"""Bounded repository tools exposed to model providers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from diffsure.git import static_diff_error

MAX_TOOL_TEXT = 50_000


@dataclass(frozen=True, slots=True)
class ToolResult:
    output: str
    is_error: bool = False


@dataclass(slots=True)
class RepositoryTools:
    root: Path
    test_requests: int = 0
    derived_checks: list[dict[str, object]] = field(default_factory=list)

    @staticmethod
    def definitions() -> list[dict[str, object]]:
        def function(
            name: str, description: str, properties: dict[str, object]
        ) -> dict[str, object]:
            return {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "additionalProperties": False,
                    },
                },
            }

        return [
            function("list_files", "List repository files", {}),
            function("read_file", "Read a UTF-8 repository file", {"path": {"type": "string"}}),
            function(
                "search_text",
                "Search UTF-8 repository files for literal text",
                {"query": {"type": "string"}},
            ),
            function(
                "apply_patch",
                "Apply a Git unified diff to the candidate workspace",
                {"diff": {"type": "string"}},
            ),
            function("git_diff", "Return the current candidate diff", {}),
            function("request_repository_tests", "Request the repository test suite", {}),
            function(
                "submit_derived_check",
                "Submit an isolated task-derived check",
                {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "command": {"type": "string"},
                },
            ),
        ]

    def dispatch(self, name: str, arguments: dict[str, object]) -> ToolResult:
        try:
            if name == "list_files":
                return ToolResult(self._list_files())
            if name == "read_file":
                return ToolResult(self._read_file(self._string(arguments, "path")))
            if name == "search_text":
                return ToolResult(self._search(self._string(arguments, "query")))
            if name == "apply_patch":
                return self._apply_patch(self._string(arguments, "diff"))
            if name == "git_diff":
                return ToolResult(self._git_diff())
            if name == "request_repository_tests":
                self.test_requests += 1
                return ToolResult("Repository test execution requested.")
            if name == "submit_derived_check":
                check: dict[str, object] = {
                    "path": self._safe_relative(self._string(arguments, "path")).as_posix(),
                    "content": self._string(arguments, "content"),
                    "command": self._string(arguments, "command"),
                }
                self.derived_checks.append(check)
                return ToolResult("Derived check accepted.")
            return ToolResult(f"unknown tool: {name}", True)
        except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
            return ToolResult(f"tool failed: {type(exc).__name__}: {str(exc)[:300]}", True)

    def _list_files(self) -> str:
        paths = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(self.root).parts
        )
        return self._bounded("\n".join(paths))

    def _read_file(self, value: str) -> str:
        path = self.root / self._safe_relative(value)
        if not path.is_file():
            raise ValueError("path is not a regular file")
        return self._bounded(path.read_text(encoding="utf-8"))

    def _search(self, query: str) -> str:
        if not query or len(query) > 500:
            raise ValueError("query length is invalid")
        matches: list[str] = []
        for relative in self._list_files().splitlines():
            path = self.root / relative
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeError:
                continue
            for number, line in enumerate(lines, 1):
                if query in line:
                    matches.append(f"{relative}:{number}:{line}")
        return self._bounded("\n".join(matches))

    def _apply_patch(self, diff: str) -> ToolResult:
        encoded = diff.encode()
        error = static_diff_error(encoded)
        if error is not None:
            return ToolResult(error, True)
        result = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            cwd=self.root,
            input=encoded,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            return ToolResult(result.stderr.decode(errors="replace")[:1000], True)
        return ToolResult("Patch applied.")

    def _git_diff(self) -> str:
        untracked = (
            subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "-z"],
                cwd=self.root,
                capture_output=True,
                timeout=10,
                check=True,
            )
            .stdout.decode("utf-8")
            .split("\0")
        )
        paths = [path for path in untracked if path]
        for offset in range(0, len(paths), 100):
            subprocess.run(
                ["git", "add", "--intent-to-add", "--", *paths[offset : offset + 100]],
                cwd=self.root,
                capture_output=True,
                timeout=10,
                check=True,
            )
        result = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--no-color"],
            cwd=self.root,
            capture_output=True,
            timeout=10,
            check=True,
        )
        return self._bounded(result.stdout.decode("utf-8"))

    def _safe_relative(self, value: str) -> PurePosixPath:
        if not value or "\\" in value or value.startswith("/"):
            raise ValueError("unsafe path")
        path = PurePosixPath(value)
        if ".." in path.parts or "." in path.parts or path.parts[0] == ".git":
            raise ValueError("unsafe path")
        return path

    @staticmethod
    def _string(arguments: dict[str, object], key: str) -> str:
        value = arguments.get(key)
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value

    @staticmethod
    def _bounded(value: str) -> str:
        return value if len(value) <= MAX_TOOL_TEXT else value[:MAX_TOOL_TEXT] + "\n[truncated]"
