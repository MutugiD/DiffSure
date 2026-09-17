# ADR-0001: Maintain an Independent Repository

- Status: accepted
- Date: 2026-09-17

## Decision

DiffSure is an independent sibling of AxiomRunner. It may apply the same general
engineering lessons but shares no package, Git history, runtime contract, or
release lifecycle.

## Consequences

The repository can match the HTTP patch contract and multi-stack boundary
without weakening another product's Python-only CLI guarantees.
