# ADR-0009: Separate the Delivery Gate

- Status: accepted
- Date: 2026-09-17

## Decision

The final gate uses a new snapshot copy, reapplies the diff, and reruns every
mandatory check through code that does not reuse the candidate workspace or
its build products.

## Consequences

Generation success cannot bypass delivery checks. Gate failure always produces
a null diff.
