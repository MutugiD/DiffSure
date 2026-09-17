"""Dependency-free repository and documentation policy checks."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLE_PATTERN = re.compile(r"^(task|feat): [a-z0-9].+")
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".sh"}
FORBIDDEN = (
    "generated " + "by " + "co" + "dex",
    "co-authored-by: " + "co" + "dex",
)
FORBIDDEN_TRACKED_PARTS = {"reviewer", ".diffsure", "results"}


def tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def check_links(path: Path, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for target in LINK_PATTERN.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = target.split("#", 1)[0]
        if clean and not (path.parent / clean).resolve().exists():
            failures.append(f"broken link in {path.relative_to(ROOT)}: {target}")


def main() -> int:
    failures: list[str] = []
    for required in (ROOT / "README.md", ROOT / "documentation" / "README.md"):
        if not required.is_file():
            failures.append(f"missing required file: {required.relative_to(ROOT)}")

    title = os.environ.get("PR_TITLE", "")
    if title and not TITLE_PATTERN.fullmatch(title):
        failures.append("pull request title must start with 'task: ' or 'feat: '")

    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if any(part.lower() in FORBIDDEN_TRACKED_PARTS for part in relative.parts):
            failures.append(f"forbidden tracked artifact: {relative}")
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"text file is not UTF-8: {relative}")
            continue
        lowered = text.lower()
        for phrase in FORBIDDEN:
            if phrase in lowered:
                failures.append(f"forbidden attribution in {relative}")
        if path.suffix == ".md":
            check_links(path, failures)

    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
