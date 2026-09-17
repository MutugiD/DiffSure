# ADR-0002: Implement the Service in Python 3.12

- Status: accepted
- Date: 2026-09-17

## Decision

Use Python 3.12 with a typed package and a standard-library HTTP boundary. Keep
runtime dependencies minimal and manage development tooling with `uv`.

## Consequences

The service language is independent of the repository language. Candidate
toolchains remain confined to the acceptance image.
