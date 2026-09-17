from __future__ import annotations

import base64
import io
import tarfile


def archive(entries: dict[str, bytes], *, kind: dict[str, str] | None = None) -> str:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as tar:
        for name, data in entries.items():
            info = tarfile.TarInfo(name)
            entry_kind = (kind or {}).get(name, "file")
            if entry_kind == "dir":
                info.type = tarfile.DIRTYPE
                info.size = 0
            elif entry_kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "target"
                info.size = 0
            else:
                info.size = len(data)
            tar.addfile(info, None if info.isdir() or info.issym() else io.BytesIO(data))
    return base64.b64encode(output.getvalue()).decode()


def repository_archive() -> str:
    return archive(
        {
            "repo/.git/HEAD": b"ref: refs/heads/main\n",
            "repo/run_tests.sh": b"exit 1\n",
            "repo/source.py": b"VALUE = 1\n",
        }
    )
