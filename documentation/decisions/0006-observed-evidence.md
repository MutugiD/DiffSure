# ADR-0006: Rank Only Observed Evidence

- Status: accepted
- Date: 2026-09-17

## Decision

Viability and ranking use static checks and sandbox observations. Provider
confidence, prose, and unexecuted claims have no score. Evidence is append-only
and retains check provenance.

## Consequences

DiffSure may prefer a smaller patch with stronger observed checks over a
provider's favored candidate.
