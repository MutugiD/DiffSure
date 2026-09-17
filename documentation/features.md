# Feature Catalogue

## Intake and control plane

- Readiness endpoint with provider, sandbox, and capacity status.
- Strict request types, body limits, and deterministic error responses.
- Safe base64, gzip, tar, path, entry, and expanded-size validation.
- Immutable pristine snapshot and isolated candidate workspaces.
- Monotonic deadline cutoffs, cancellation, and cleanup ownership.

## Reasoning and tool plane

- Local Ollama and explicit OpenAI provider adapters.
- Normalized assistant text, local tool calls, tool results, and usage.
- Bounded repository listing, reading, search, patch, diff, and check tools.
- Repository-content prompt-injection boundary.
- Independent task-derived test design.
- Diverse candidate lineages and counterexample-driven repair.

## Evidence and delivery plane

- Exact public static diff validation.
- Clean application against the received snapshot.
- Multi-toolchain repository tests through root `run_tests.sh`.
- Ephemeral derived checks outside the delivered diff.
- Resource-limited networkless container execution.
- Append-only evidence, failure classification, and deterministic ranking.
- Independent fresh-snapshot final gate and fail-closed null response.

## Operations and delivery plane

- Three-request capacity control and per-request isolation.
- Structured redacted logs and phase metrics.
- Provider usage and estimated-cost reporting.
- Python package, service image, and Compose operation.
- Pull-request CI and GHCR publication from protected `main` and version tags.
- Diagnostics, public benchmark report, and production runbooks.

## Supported matrix

| Capability | Version 0.1.0 |
| --- | --- |
| Python service runtime | Supported |
| Python repository tasks | Supported |
| JavaScript repository tasks | Supported |
| Bash repository tasks | Supported |
| Go repository tasks | Supported |
| C repository tasks | Supported |
| Rust repository tasks | Supported |
| Java repository tasks | Supported |
| Local Ollama inference | Default |
| Explicit OpenAI inference | Supported |
| Automatic paid fallback | Prohibited |
| Web-enabled model tools | Prohibited |
| Host candidate execution | Prohibited |
| Docker acceptance sandbox | Required for viable delivery |

## Roadmap

1. Service and health bootstrap.
2. Request, archive, workspace, budget, Git, and static-diff foundation.
3. Provider normalization and repository tool loop.
4. Isolated multi-stack verification and independent checks.
5. First end-to-end verified patch.
6. Candidate diversification and repair.
7. Concurrent operations, packaging, and release evidence.
