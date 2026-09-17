from __future__ import annotations

import base64
from pathlib import Path

import pytest

from diffsure.archive import RepositoryWorkspace
from diffsure.config import Settings
from diffsure.domain import RequestError
from tests.helpers import archive, repository_archive


def settings(**changes: object) -> Settings:
    values: dict[str, object] = {
        "host": "127.0.0.1",
        "port": 0,
        "provider": "ollama",
        "model": "model",
        "provider_url": "url",
        "acceptance_image": "image",
        "capacity": 3,
        "health_skip_external": True,
    }
    values.update(changes)
    return Settings(**values)  # type: ignore[arg-type]


def test_repository_materializes_and_cleans_up() -> None:
    with RepositoryWorkspace(repository_archive(), settings()) as repo:
        path = repo
        assert (repo / "source.py").read_text() == "VALUE = 1\n"
    assert not path.exists()


@pytest.mark.parametrize("encoded", ["not-base64", base64.b64encode(b"no").decode()])
def test_invalid_encoding_rejected(encoded: str) -> None:
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings()):
        pass


@pytest.mark.parametrize(
    "encoded",
    [
        archive({"outside": b"x"}),
        archive({"repo/../outside": b"x"}),
        archive({"repo\\outside": b"x"}),
        archive({"repo/link": b""}, kind={"repo/link": "symlink"}),
        archive({"repo/run_tests.sh": b"x"}),
        archive({"repo/.git/HEAD": b"x"}),
    ],
)
def test_unsafe_or_incomplete_repository_rejected(encoded: str) -> None:
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings()):
        pass


def test_archive_limits_are_enforced() -> None:
    encoded = repository_archive()
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings(max_archive_bytes=2)):
        pass
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings(max_archive_entries=1)):
        pass
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings(max_extracted_bytes=2)):
        pass
    with pytest.raises(RequestError), RepositoryWorkspace(encoded, settings(max_path_depth=2)):
        pass


def test_path_type_is_local_path() -> None:
    with RepositoryWorkspace(repository_archive(), settings()) as repo:
        assert isinstance(repo, Path)
