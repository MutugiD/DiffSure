# DiffSure: End-to-End Repository, PR, Product, and Release Plan

## Summary

Build DiffSure as a Python 3.12 autonomous patch service in:

`D:\clients-ops\proposals\ChallengeBox\DiffSure`

The public remote is:

`https://github.com/MutugiD/DiffSure.git`

The local directory and remote currently exist but are empty. Establish `main` with the requested bootstrap commit as the only direct push. After that, deliver all documentation, architecture, CI/CD, product requirements, features, implementation, validation, and release through strictly sequential PRs.

AxiomRunner remains an independent sibling. Its deadline, evidence, sandbox, and repair lessons inform DiffSure’s design, but no AxiomRunner code, Git history, or uncommitted changes are reused.

## Repository Bootstrap

Run the requested initialization from the existing empty `DiffSure` directory:

```powershell
Set-Location D:\clients-ops\proposals\ChallengeBox\DiffSure

echo "# DiffSure" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/MutugiD/DiffSure.git
git push -u origin main
```

Bootstrap verification:

```powershell
git status --short --branch
git remote -v
git log --oneline --decorate -1
git ls-remote --heads origin main
```

Expected state:

- Local branch is `main`.
- Working tree is clean.
- `origin` points to `MutugiD/DiffSure`.
- Local and remote `main` reference the same initial commit.
- `first commit` is the only commit exempt from the later `task:`/`feat:` naming policy.

Do not copy anything from `Challenge2/reviewer` into DiffSure. Development and acceptance runs use only the candidate brief, public harness, public tasks, and supplied acceptance environment.

## Mandatory Sequential PR Workflow

Only one feature branch and one PR may be active at a time. No stacked PRs, parallel feature branches, or work based on an unmerged predecessor.

### Start every PR

```powershell
git switch main
git pull --ff-only origin main
git status --short
git switch -c <task-or-feat>/<short-name>
```

The working tree must be clean before branching.

### Complete every PR

1. Implement only that PR’s documented scope.
2. Run its complete local quality and acceptance gates.
3. Confirm no secrets, temporary results, generated candidate code, reviewer files, or attribution language are included.
4. Commit using `task: ...` or `feat: ...`.
5. Push the branch and create the PR with the same compliant title.
6. Watch all CI checks and review threads until they reach a terminal state.
7. For a failed check:
   - Inspect the failing job and reproduce it locally where possible.
   - Fix the root cause on the same branch.
   - Run the complete affected gate locally.
   - Push the correction and watch the replacement run.
8. For requested changes:
   - Address each comment on the same branch.
   - Add or update tests when behavior changes.
   - Reply with the concrete resolution.
   - Resolve the thread only after the fix is pushed.
9. Merge only when all required checks are green and no change request or unresolved blocking thread remains.
10. Squash-merge using the PR title as the main-branch commit message.
11. Watch the post-merge `main` workflow and any applicable CD publication until green.
12. Synchronize locally before starting the next PR:

```powershell
git switch main
git pull --ff-only origin main
git branch -d <task-or-feat>/<short-name>
git status --short --branch
```

Delete the remote feature branch after merging. If post-merge CI fails, repair `main` through a dedicated sequential `task:` PR before starting the next planned PR.

## Architecture and Product Contract

### HTTP interfaces

`GET /health`

- Return `200` only when the service can accept work and the configured provider, Git, and Docker runtime are ready.
- Return a small JSON readiness body with provider, model, sandbox image, capacity, and status.
- Never expose secrets or host paths.

`POST /solve`

Request:

```json
{
  "request_id": "string",
  "repo_archive_b64": "base64 tar.gz Git repository",
  "task": "string",
  "deadline_seconds": 240
}
```

Success or fail-closed response:

```json
{
  "request_id": "string",
  "diff": "unified diff or null",
  "record": [],
  "usage": {
    "provider": "ollama or openai",
    "model": "string",
    "input_tokens": 0,
    "output_tokens": 0,
    "estimated_cost_usd": 0.0,
    "elapsed_seconds": 0.0
  }
}
```

- A non-null diff must have passed the independent clean-copy delivery gate.
- Expected solve failures return a timely `200` with `diff: null` and an auditable record.
- Invalid HTTP/JSON/base64/archive input returns a deterministic `4xx` response.
- Unexpected service faults return a sanitized `5xx` response without leaking repository content.

### Provider policy

- `DIFFSURE_PROVIDER=ollama|openai`; default `ollama`.
- Ollama default model: `qwen3:8b`.
- OpenAI default model: `gpt-5.6-terra` through the Responses API.
- `DIFFSURE_MODEL` overrides the provider default.
- OpenAI is explicitly selected, never an automatic paid fallback.
- Hosted requests use `store: false` and expose only local custom tools—no web search, hosted file search, or external repository lookup.
- Provider secrets are environment-only and redacted from records and logs.

### Bottom-up architecture

1. Domain values:
   - `SolveRequest`, `SolveBudget`, `RepositorySnapshot`, `ToolCall`, `ModelTurn`, `DerivedCheck`, `Candidate`, `CheckResult`, `Evidence`, `Usage`, and `SolveResponse`.
   - Immutable identifiers and append-only evidence.
2. Infrastructure ports:
   - Model provider, monotonic clock, Git adapter, workspace store, container runner, recorder, and cost calculator.
3. Core services:
   - Request validation, archive ingestion, repository inventory, test design, candidate generation, static diff validation, sandbox verification, evidence ranking, repair, and final delivery gating.
4. Orchestration:
   - One state machine owns every solve transition and deadline.
   - Candidate workspaces derive from one immutable snapshot.
   - Model assertions never count as verification evidence.
5. Delivery:
   - Standard-library Python HTTP service.
   - Docker CLI drives disposable sibling containers.
   - Repository and check archives are streamed into container tmpfs; candidate code is never executed or imported on the host.

### Solve workflow

1. Validate request size, JSON types, identifier, deadline, and base64.
2. Extract one `repo/` root while rejecting traversal, symlinks, hardlinks, devices, excessive entries, and decompression bombs.
3. Establish an absolute monotonic deadline and a 10% final-response reserve bounded to 10–30 seconds.
4. Inspect repository structure and existing tests with read-only tools.
5. Run the baseline suite inside the supplied acceptance image.
6. Have an independent test-design role produce at least one executable task-derived check before seeing candidate source.
7. Run one candidate session and start a second diversified session only when the remaining budget permits.
8. Let agents list, read, search, patch, inspect diffs, and request containerized checks. They receive no web or host-shell access.
9. Apply the exact public UTF-8, LF, size, binary, symlink, path, and `git apply --check` rules.
10. Run the repository suite and every derived check in the networkless acceptance container.
11. Classify failures and perform bounded repairs before the repair cutoff.
12. Rank viable candidates by observed evidence, coverage of derived checks, runtime, diff size, and stable candidate ID.
13. Apply the selected diff to a fresh untouched snapshot through a separate delivery-gate path.
14. Rerun static validation, repository tests, and derived checks.
15. Return the diff only if the clean gate passes before the protected response reserve; otherwise return `null`.

The wire request does not include `task.json`, despite the brief referring to its `test_command`. Every supplied repository snapshot includes a root `run_tests.sh` containing the correct language-specific command. DiffSure therefore executes `bash run_tests.sh` and fails closed when that contract is absent. This discrepancy is recorded in an ADR and contract tests.

## Sequential PR Roadmap

### PR 1 — `task: establish documentation and CI foundation`

Branch: `task/documentation-ci-foundation`

Deliver:

- Replace the bootstrap README with product summary, status, documentation links, and development entry points.
- Add `/documentation/README.md`, context, problem map, glossary, acceptance overview, and documentation conventions.
- Add `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `.editorconfig`, `.gitattributes`, `.gitignore`, and PR template.
- Add repository policy validation:
  - PR titles and commits must begin with `task:` or `feat:`.
  - Reject attribution or generated-by language.
  - Reject tracked secrets, benchmark outputs, temporary workspaces, and reviewer artifacts.
  - Require README and documentation index.
- Add initial GitHub Actions:
  - Repository policy and documentation checks on PRs and `main`.
  - Dependency review on PRs.
  - CodeQL-ready permissions and least-privilege defaults.
  - CD workflow definition with publication disabled until the service Dockerfile exists.
- Merge gate:
  - All initial policy and documentation checks pass.
  - After merge, configure `main` protection using the newly established required checks.

### PR 2 — `task: define detailed system architecture`

Branch: `task/detailed-system-architecture`

Deliver:

- System context, container, component, and deployment architecture.
- Bottom-up drill-down from immutable values through ports, services, orchestration, and deployment.
- Normal solve, repair, deadline, failure, concurrency, container execution, and clean-delivery workflows.
- Threat model covering hostile archives, hostile repositories, generated source, prompt injection, secret exposure, Docker access, path escape, and denial of service.
- Initial accepted ADRs:
  - Independent DiffSure repository.
  - Python 3.12 service.
  - Ollama and explicit OpenAI provider adapters.
  - Supplied multi-toolchain acceptance image.
  - Streamed container workspaces.
  - Observed-evidence ranking.
  - Protected deadline reserve.
  - Root `run_tests.sh` contract.
  - Clean-copy independent gate.
- Merge gate:
  - Documentation links and Mermaid syntax validate.
  - Every public requirement maps to an architectural component and workflow.

### PR 3 — `feat: define product requirements and feature map`

Branch: `feat/product-requirements-feature-map`

Deliver:

- Product requirements document with user, goals, non-goals, constraints, success metrics, and failure behavior.
- Feature catalogue:
  - HTTP intake and health.
  - Safe repository ingestion.
  - Provider abstraction.
  - Repository tool loop.
  - Independent test design.
  - Candidate generation.
  - Exact diff validation.
  - Multi-stack sandbox verification.
  - Multiple candidates and repairs.
  - Evidence ranking.
  - Independent delivery gate.
  - Usage and cost reporting.
  - Concurrency, health, logging, packaging, CI/CD, and release evidence.
- Supported matrix covering Python, JavaScript, Bash, Go, C, Rust, and Java task repositories.
- Public acceptance criteria and production scaling, monitoring, cost-control, and contract-versioning plans.
- Traceability table mapping every requirement to its planned PR and test category.
- Merge gate:
  - No application code exists yet.
  - Requirements, features, acceptance tests, and architecture are mutually traceable.

### PR 4 — `task: bootstrap the Python service`

Branch: `task/python-service-bootstrap`

Deliver:

- `pyproject.toml`, `uv.lock`, `src/diffsure`, and test layout.
- Typed configuration and structured redacted logging.
- Standard-library HTTP server with routing and graceful shutdown.
- End-to-end `/health` readiness slice.
- Service Dockerfile and Compose configuration.
- Docker socket integration and provider connectivity configuration.
- CI expansion:
  - Ruff format and lint.
  - Strict mypy.
  - Pytest with coverage threshold.
  - Package build.
  - Dependency audit.
  - Service-image build and health smoke test.
- CD activation:
  - PRs build without publishing.
  - `main` publishes `ghcr.io/mutugid/diffsure:<commit-sha>` and `edge`.
  - `v*` tags publish the semantic version and `latest`.
- Merge gate:
  - Local and containerized health checks pass.
  - Main publication is verified after merge.

### PR 5 — `feat: ingest solve requests and repository snapshots`

Branch: `feat/solve-request-ingestion`

Deliver:

- Typed request/response parsing and deterministic HTTP errors.
- Base64 and gzip validation.
- Configurable compressed, extracted-size, entry-count, and path-depth limits.
- Safe extraction with link, device, absolute-path, and traversal rejection.
- Immutable pristine snapshot plus per-candidate workspaces.
- Monotonic solve budget and cancellation propagation.
- Git adapter and exact public static-diff rules.
- End-to-end slice: valid request becomes a safe workspace and returns an intentional recorded `null` diff.
- Merge gate:
  - Archive attack corpus passes.
  - Malformed requests never create residual workspaces.
  - No repository content executes on the host.

### PR 6 — `feat: add model providers and repository tools`

Branch: `feat/model-providers-repository-tools`

Deliver:

- Provider protocol and normalized model turn, tool call, token usage, latency, and error types.
- Ollama adapter using `qwen3:8b`.
- OpenAI Responses adapter using `gpt-5.6-terra`.
- Deterministic fake provider for CI.
- Bounded tools for file listing, reading, search, patch application, Git diff, repository test requests, and derived-check requests.
- Ordered challenge-compatible public `record`.
- Prompt-injection boundaries: repository text is data, never service policy.
- End-to-end slice: fake provider inspects and patches a fixture repository, with every turn and tool result recorded.
- Merge gate:
  - Provider failures and malformed tool calls fail closed.
  - Records preserve ordering and redact configuration and secrets.

### PR 7 — `feat: add isolated verification and derived checks`

Branch: `feat/isolated-verification`

Deliver:

- Disposable acceptance-container runner using streamed tar input.
- Network disabled, non-root user, read-only root, tmpfs work areas, CPU, memory, process, and deadline limits.
- Root `run_tests.sh` repository-suite execution.
- Independent test-designer role isolated from candidate source.
- Ephemeral derived-check files stored outside the repository diff.
- Static and dynamic `CheckResult` evidence.
- Fixture verification for all seven toolchains.
- End-to-end slice: a prepared patch passes repository and independently generated checks without host execution.
- Merge gate:
  - Sandbox-control integration tests pass.
  - Derived checks cannot appear in the delivered diff.
  - Infrastructure failures remain distinguishable from candidate failures.

### PR 8 — `feat: deliver the first verified patch workflow`

Branch: `feat/verified-patch-workflow`

Deliver:

- Candidate lifecycle and lineage.
- Tool-driven source modification and unified-diff creation.
- Exact static gate before dynamic execution.
- Evidence-based viability rules.
- Fresh untouched-snapshot delivery gate implemented through a separate code path.
- Atomic response finalization and `null` fallback.
- First complete vertical slice:
  - HTTP request.
  - Repository inspection.
  - Candidate patch.
  - Repository and derived checks.
  - Clean-copy apply and rerun.
  - Non-null HTTP diff response.
  - Official harness acceptance for deterministic fixtures.
- Merge gate:
  - No diff is returned when any mandatory clean-gate check fails.
  - Returned diffs apply cleanly to their original snapshots.

### PR 9 — `feat: add candidate diversification and repair`

Branch: `feat/candidate-diversification-repair`

Deliver:

- Up to two independently prompted candidate lineages.
- Budget-aware candidate cutoff and repair cutoff.
- Structural, behavioral, resource, infrastructure, and inconclusive failure classification.
- Bounded repair using original task, parent diff, observed failures, and minimized counterexamples.
- Deterministic evidence ranking and stable tie-breaking.
- Preservation of the strongest already verified candidate as deadlines approach.
- End-to-end scenarios:
  - First candidate fails and repair succeeds.
  - First candidate fails and second candidate wins.
  - Later candidate is weaker and earlier verified candidate is retained.
  - Deadline prevents further work and best verified diff is returned.
- Merge gate:
  - No new model work starts after its cutoff.
  - Repair never consumes finalization reserve.

### PR 10 — `feat: harden concurrent service operation`

Branch: `feat/concurrent-service-operation`

Deliver:

- Complete solve state machine and capacity manager.
- Three concurrent HTTP solve requests.
- Per-request isolation, cancellation, cleanup, and deadlines.
- Provider concurrency controls and Ollama queue behavior.
- Health readiness reflecting service capacity and dependencies.
- Structured operational metrics:
  - Request count and outcome.
  - Phase latency.
  - Deadline pressure.
  - Candidate and repair counts.
  - Static, apply, test, and delivery-gate outcomes.
  - Provider tokens and estimated cost.
- Graceful shutdown without returning partial diffs.
- Contract-version isolation for future breaking request changes.
- Merge gate:
  - Three-request concurrency integration suite passes.
  - One failed or timed-out request cannot contaminate another.

### PR 11 — `feat: complete packaging and operational delivery`

Branch: `feat/packaging-operational-delivery`

Deliver:

- Final Compose workflow for Ollama and OpenAI modes.
- Provider, Docker, image, and Git diagnostics.
- Runbooks for installation, local service operation, public harness execution, troubleshooting, and cost control.
- GHCR image metadata, labels, provenance, SBOM, and vulnerability scan.
- Production note covering horizontal workers, provider rate limits, queueing, monitoring, secret management, storage, and API version migration.
- End-to-end smoke test using the published GHCR image.
- Merge gate:
  - Fresh-environment instructions produce a healthy service.
  - Published image runs without source checkout.

### PR 12 — `task: validate public acceptance and release`

Branch: `task/public-acceptance-release`

Deliver:

- Build the supplied `acceptance:latest` image.
- Run the official public harness at concurrency three.
- Run local Ollama evidence first.
- Run the OpenAI `gpt-5.6-terra` benchmark with an out-of-band key.
- Add `results.md` containing:
  - Per-task outcome and duration.
  - Static/apply/test stage results.
  - Null and deadline rates.
  - Provider, model, tokens, and estimated request cost.
  - Aggregate acceptance and cost.
  - Clearly separated local and hosted results.
- Verify README, architecture summary, trade-offs, run instructions, and production note satisfy every deliverable.
- Tag `v0.1.0` only after the PR merges and post-merge CI/CD is green.
- Watch the tag workflow until the versioned and `latest` GHCR images publish successfully.
- Final release gate:
  - 7/7 public tasks accepted.
  - Zero pre-execution rejections.
  - Zero missed deadlines.
  - Zero null diffs.
  - Concurrency three succeeds.
  - All CI, security, image, documentation, and release checks are green.

## Test Strategy

- Unit:
  - Schemas, configuration, redaction, archive safety, Git operations, diff rules, budgets, state transitions, scoring, provider normalization, usage, and cost.
- Contract:
  - Exact `/health`, `/solve`, record, diff, and failure shapes.
  - Compatibility with `harness/run_client.py`.
- Integration:
  - Fake provider, real Git repositories, candidate workspaces, repair paths, clean gate, and concurrent requests.
- Sandbox:
  - Network denial, non-root user, read-only root, tmpfs, CPU/memory/process limits, timeout termination, and no host execution.
- Multi-stack:
  - Python, JavaScript, Bash, Go, C, Rust, and Java repository suites through `run_tests.sh`.
- Adversarial:
  - Malicious archives, restricted diff paths, symlinks, binary patches, oversized diffs, prompt injection, secret requests, hanging tests, fork bombs, and malformed provider output.
- Live acceptance:
  - Official public tasks only.
  - Reviewer-only files are never used for development, prompting, verification, or release reporting.

## Assumptions and Fixed Decisions

- The requested direct bootstrap commit creates `main`; every later repository change uses the sequential PR workflow.
- The repository is intentionally public.
- Python 3.12 and `uv` are the development baseline.
- Ollama is the zero-cost default; OpenAI is an explicit stronger-provider option.
- An OpenAI key will be supplied outside the repository for the hosted benchmark.
- CD publishes to GHCR; no runtime deployment target has been specified.
- Branch protection begins after PR 1 creates stable named checks.
- Merge requires green checks and no unresolved blocking review, but does not require an approval if no human reviewer has been assigned.
- AxiomRunner and Challenge2 remain unchanged.
