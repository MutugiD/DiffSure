# ADR-0005: Stream Workspaces into Containers

- Status: accepted
- Date: 2026-09-17

## Decision

Send repository and check archives over container standard input and extract
them into tmpfs. Do not bind-mount service paths into candidate containers.

## Consequences

The service can run inside its own container without requiring its filesystem
paths to exist on the Docker host.
