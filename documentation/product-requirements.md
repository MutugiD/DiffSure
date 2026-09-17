# Product Requirements

## Product statement

DiffSure turns a repository snapshot and change request into the strongest
independently verified unified diff it can produce before a fixed deadline.
Correctness evidence and timely fail-closed behavior take priority over model
confidence and conversational output.

## Primary user

The primary user operates an automated private acceptance pipeline and needs a
service that remains reachable, returns contract-valid responses, and never
delivers a patch it has not independently checked.

## Goals

- Accept the published `/solve` contract and remain healthy under three
  concurrent requests.
- Support repository suites in Python, JavaScript, Bash, Go, C, Rust, and Java.
- Build independent evidence when private acceptance tests are unavailable.
- Deliver only a diff that applies to the exact snapshot and passes a separate
  clean-copy gate.
- Preserve a complete ordered model/tool record and observed usage.
- Respect every declared deadline with a protected response reserve.
- Run generated code only in the supplied offline acceptance environment.

## Non-goals

- Reading or inferring reviewer-only acceptance material.
- Executing repository code on the host.
- Searching the web or downloading dependencies during a solve.
- Guaranteeing hidden-test correctness.
- Automatically switching to a paid provider.
- Modifying, committing to, or submitting changes into the received repository.

## Functional requirements

| ID | Requirement |
| --- | --- |
| FR-01 | Expose readiness through `GET /health`. |
| FR-02 | Validate and bound every `/solve` wire field before work begins. |
| FR-03 | Extract exactly one safe repository root from the archive. |
| FR-04 | Allocate absolute monotonic phase cutoffs and a protected response reserve. |
| FR-05 | Inspect repositories only through bounded local tools. |
| FR-06 | Normalize Ollama and explicitly selected OpenAI model turns and usage. |
| FR-07 | Design at least one executable task-derived check without candidate source. |
| FR-08 | Produce one candidate and a second diverse candidate when budget permits. |
| FR-09 | Mirror all public static diff and clean-apply rules. |
| FR-10 | Execute repository and derived checks only in the configured sandbox. |
| FR-11 | Repair structural or behavioral failures before the repair cutoff. |
| FR-12 | Rank candidates using observed evidence and deterministic tie-breaking. |
| FR-13 | Reapply and reverify the selected diff through an independent clean-copy gate. |
| FR-14 | Return only a gate-passing diff; otherwise return a timely null diff. |
| FR-15 | Return an ordered public record and provider usage without secrets. |
| FR-16 | Isolate and clean up concurrent solve state. |

## Quality requirements

- **Safety:** no candidate execution on the host and no candidate access to the
  Docker socket, network, provider credentials, or other workspaces.
- **Timeliness:** external operations are clamped to absolute phase deadlines.
- **Availability:** expected model or candidate failures still yield a complete
  response before the request deadline.
- **Auditability:** every delivered diff has traceable static, dynamic, and gate
  evidence.
- **Determinism:** configuration, evidence ordering, scoring, and tie-breaking
  are stable; model kernels may remain nondeterministic.
- **Portability:** the host service supports Windows and Linux while sandbox
  execution uses the supplied Linux image.
- **Maintainability:** typed ports isolate HTTP, providers, Git, storage,
  containers, clocks, recording, and cost calculation.

## Failure behavior

Malformed requests fail with deterministic 4xx responses before inference.
Provider, sandbox, no-candidate, or gate failures return a recorded null diff
when the wire request is valid. Internal details, secrets, and host paths are
never returned.

## Release success metrics

- Seven of seven public tasks accepted at concurrency three.
- Zero static or apply rejections.
- Zero missed deadlines and null diffs in the release run.
- All deterministic CI, container, package, security, and documentation checks
  green.
- Reproducible per-request latency, token, model, provider, and cost evidence.
