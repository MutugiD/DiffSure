# DiffSure

DiffSure is a deadline-aware service that turns a repository snapshot and a
change request into an independently verified unified diff. Candidate code is
never executed on the host: tests and derived checks run in the supplied
networkless, resource-limited multi-toolchain container.

The project is delivered documentation-first. Begin with the
[documentation index](documentation/README.md), then read the
[challenge context](documentation/context.md) and
[problem-to-solution map](documentation/problem-map.md).

## Status

The Python service exposes dependency diagnostics, capacity-aware `GET /health`,
and the complete fail-closed `POST /solve` workflow. Every returned diff has
passed static validation, repository and independent checks, and a separate
fresh-copy delivery gate.

## Delivery policy

Work is delivered through one sequential pull request at a time. Pull request
titles and commit subjects begin with `task:` or `feat:`. Each pull request must
be green and free of unresolved blocking review before it is squash-merged to
`main`.

## Development

Python 3.12, `uv`, Git, Docker, and the supplied `acceptance:latest` image are
the intended toolchain.

```text
uv sync --locked --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

Run diagnostics or start the service:

```text
uv run diffsure doctor
uv run diffsure serve
```

For Compose, provider modes, published images, the public harness,
troubleshooting, and cost controls, follow the
[operational runbooks](documentation/runbooks.md).

For a containerized development smoke test that does not probe host services,
set `DIFFSURE_HEALTH_SKIP_EXTERNAL=1`. This flag is not intended for deployed
readiness checks.

## License

DiffSure is available under the [MIT License](LICENSE).
