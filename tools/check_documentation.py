"""Validate the documentation index, local links, and expected structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "documentation"
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")
REQUIRED = (
    ROOT / "README.md",
    DOCS / "README.md",
    DOCS / "context.md",
    DOCS / "problem-map.md",
    DOCS / "acceptance.md",
)


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"missing documentation: {path.relative_to(ROOT)}")

    for path in (ROOT / "README.md", *sorted(DOCS.glob("*.md"))):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            failures.append(f"missing level-one heading: {path.relative_to(ROOT)}")
        for target in LINK_PATTERN.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).resolve().exists():
                failures.append(f"broken link in {path.relative_to(ROOT)}: {target}")

    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
