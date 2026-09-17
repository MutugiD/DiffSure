"""Require UTF-8, LF-only text for tracked source and documentation files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".sh", ".txt"}


def main() -> int:
    failures: list[str] = []
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode()
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        data = path.read_bytes()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            failures.append(f"not UTF-8: {path.relative_to(ROOT)}")
        if b"\r\n" in data or b"\r" in data:
            failures.append(f"not LF-only: {path.relative_to(ROOT)}")
        if data and not data.endswith(b"\n"):
            failures.append(f"missing final newline: {path.relative_to(ROOT)}")

    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
