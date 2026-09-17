# ADR-0004: Verify in the Supplied Acceptance Image

- Status: accepted
- Date: 2026-09-17

## Decision

All repository and derived checks run in the supplied multi-toolchain image
with networking disabled, non-root execution, a read-only root, tmpfs work
areas, and explicit CPU, memory, process, output, and time limits.

## Consequences

Docker is a required runtime dependency. A host-only pass cannot make a
candidate viable.
