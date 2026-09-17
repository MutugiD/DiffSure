from __future__ import annotations

from diffsure.config import Settings
from diffsure.solve import IngestionSolver
from tests.helpers import repository_archive


def test_ingestion_solver_returns_auditable_null() -> None:
    settings = Settings("127.0.0.1", 0, "ollama", "model", "url", "image", 3, True)
    response = IngestionSolver(settings).solve(
        {
            "request_id": "id",
            "repo_archive_b64": repository_archive(),
            "task": "fix source",
            "deadline_seconds": 180,
        }
    )
    assert response.request_id == "id"
    assert response.diff is None
    assert response.record[0]["role"] == "assistant"
    assert response.usage.elapsed_seconds >= 0
