"""Bounded repository archive decoding and safe materialization."""

from __future__ import annotations

import base64
import binascii
import io
import shutil
import tarfile
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path, PurePosixPath
from types import TracebackType

from diffsure.config import Settings
from diffsure.domain import RequestError


class RepositoryWorkspace(AbstractContextManager[Path]):
    def __init__(self, encoded: str, settings: Settings) -> None:
        self._encoded = encoded
        self._settings = settings
        self._temporary: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        archive = self._decode()
        self._temporary = tempfile.TemporaryDirectory(prefix="diffsure-")
        destination = Path(self._temporary.name) / "repo"
        destination.mkdir()
        try:
            self._extract(archive, destination)
            if not (destination / ".git").is_dir():
                raise RequestError("archive repository is not a Git snapshot", 422)
            if not (destination / "run_tests.sh").is_file():
                raise RequestError("archive repository lacks run_tests.sh", 422)
            return destination
        except Exception:
            self._temporary.cleanup()
            self._temporary = None
            raise

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def _decode(self) -> bytes:
        try:
            archive = base64.b64decode(self._encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RequestError("repo_archive_b64 is not valid base64") from exc
        if not archive or len(archive) > self._settings.max_archive_bytes:
            raise RequestError("repository archive size is outside the allowed range", 413)
        if not archive.startswith(b"\x1f\x8b"):
            raise RequestError("repository archive must be gzip-compressed tar")
        return archive

    def _extract(self, archive: bytes, destination: Path) -> None:
        try:
            source = tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz")  # noqa: SIM115
        except (tarfile.TarError, OSError) as exc:
            raise RequestError("repository archive is not a valid tar.gz") from exc
        seen: set[tuple[str, ...]] = set()
        total = 0
        with source:
            members = source.getmembers()
            if len(members) > self._settings.max_archive_entries:
                raise RequestError("repository archive has too many entries", 413)
            for member in members:
                parts = self._parts(member.name)
                if parts in seen:
                    raise RequestError("repository archive contains duplicate paths")
                seen.add(parts)
                if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                    raise RequestError("repository archive contains an unsupported entry")
                if not (member.isdir() or member.isfile()):
                    raise RequestError("repository archive contains an unsupported entry")
                total += member.size
                if total > self._settings.max_extracted_bytes:
                    raise RequestError("repository archive expands beyond the byte limit", 413)
                target = destination.joinpath(*parts[1:])
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = source.extractfile(member)
                if extracted is None:
                    raise RequestError("repository archive file cannot be read")
                with extracted, target.open("wb") as output:
                    shutil.copyfileobj(extracted, output)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)

    def _parts(self, name: str) -> tuple[str, ...]:
        if "\\" in name or name.startswith("/"):
            raise RequestError("repository archive contains an unsafe path")
        path = PurePosixPath(name)
        parts = path.parts
        if not parts or parts[0] != "repo" or ".." in parts or "." in parts:
            raise RequestError("repository archive must contain one repo root")
        if len(parts) > self._settings.max_path_depth:
            raise RequestError("repository archive path is too deep", 413)
        return parts
