# Threat Model

## Assets and trust boundaries

Assets include model credentials, the Docker socket, service availability,
other request workspaces, and the integrity of delivered diffs and records.
Untrusted inputs include HTTP bodies, archives, repository files, task text,
model output, generated code, generated checks, and subprocess output.

## Threats and controls

| Threat | Controls |
| --- | --- |
| Archive traversal or link escape | Single-root validation, normalized relative paths, link/device rejection, entry and size limits |
| Decompression denial of service | Compressed and expanded byte limits plus bounded entry count and depth |
| Repository prompt injection | Repository text is delimited data; only service-defined tools and policy are executable |
| Host code execution | No imports or test commands on host; all dynamic work runs in the sandbox |
| Sandbox escape impact | Non-root, no network, read-only root, tmpfs, dropped access to service and Docker socket |
| Fork bomb or resource exhaustion | CPU, memory, process, output, and monotonic time limits |
| Cross-request contamination | Per-solve directories, containers, records, budgets, and cleanup ownership |
| Secret exfiltration | Candidate receives no provider environment, host mounts, network, or service logs |
| Malicious diff | Exact static rules, clean apply, forbidden paths, no binaries or symlinks |
| False verification | Independent checks, append-only evidence, and separate clean-copy gate |
| Paid-provider surprise | Explicit provider selection; no automatic hosted fallback |
| Record leakage | Bounded outputs, normalized paths, secret redaction, no internal reasoning export |
| Docker-socket compromise | Only the service-side runner can access it; candidate containers never can |

## Residual risks

The service cannot prove hidden-test correctness, a Docker daemon compromise is
host-significant, model providers may retain data according to account policy,
and resource limits depend on the host daemon enforcing them. Operations must
monitor these assumptions and fail closed when controls cannot be established.
