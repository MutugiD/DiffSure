# ADR-0008: Use the Root Test Wrapper

- Status: accepted
- Date: 2026-09-17

## Context

The brief refers to `task.json`, but that file is absent from the wire request
and packed repository. Every supplied snapshot contains `run_tests.sh`.

## Decision

Execute `bash run_tests.sh` inside the acceptance image. Fail closed if it is
missing, not a regular file, or cannot run within the budget.

## Consequences

All supplied languages use their intended command without guessing from file
extensions. The discrepancy remains visible rather than silently invented.
