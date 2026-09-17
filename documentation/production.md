# Production Evolution

## Scaling

Place stateless HTTP replicas behind a load balancer and admit work through a
bounded queue. Route local-model jobs to workers with dedicated inference
capacity; route hosted jobs through account-aware rate limiters. Give every job
an isolated temporary volume and container namespace.

## Monitoring

Measure request outcomes, admission delay, phase latency, cutoff activation,
provider latency and tokens, candidate counts, repair counts, static/apply/test
failures, clean-gate failures, sandbox resource use, null responses, and missed
deadlines. Alert on availability, deadline, and acceptance regressions rather
than model prose.

## Cost control

Keep local Ollama as the default, require explicit hosted-provider selection,
cap provider output and calls per phase, reuse stable prompt prefixes, record
actual token usage, and stop low-evidence work at deterministic cutoffs. Apply
per-tenant concurrency and spend limits before admission.

## Security and storage

Store provider credentials in a secret manager, isolate the Docker control
plane from candidate containers, encrypt retained reports, expire repository
snapshots promptly, and redact task content from aggregate telemetry. Retain
only evidence required by the operating policy.

## Contract evolution

The current contract identifier is `v1`. Responses include
`X-DiffSure-Contract: v1`; callers may send the same header, while unknown
versions fail deterministically before solve execution. Add a versioned endpoint
for breaking wire changes, keep the current serializer during a deprecation
window, and publish compatibility fixtures before routing traffic to a new
version.

## Runtime capacity and metrics

Solve admission and provider concurrency are independent. The service admits up
to `DIFFSURE_CAPACITY` isolated requests; `DIFFSURE_PROVIDER_CAPACITY` bounds
simultaneous model calls and defaults to one for Ollama. Readiness becomes false
while all solve slots are occupied or shutdown is in progress.

The synchronized operational snapshot contains request outcomes, phase counts
and latency, deadline pressure, candidate and repair counts, verification
outcomes, provider tokens, elapsed time, and estimated cost. It contains no
repository content, prompts, diffs, credentials, or host paths. A production
exporter can translate this snapshot to the deployment's monitoring system.
