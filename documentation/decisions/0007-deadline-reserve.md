# ADR-0007: Protect a Final Response Reserve

- Status: accepted
- Date: 2026-09-17

## Decision

Use a monotonic clock and reserve ten percent of the deadline, bounded to 10–30
seconds, for selection, the clean gate, serialization, and response delivery.
Stop new candidates and repairs at earlier absolute cutoffs.

## Consequences

The service intentionally stops improving before the client deadline so a
complete verified response can still be delivered.
