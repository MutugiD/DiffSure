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

Add a versioned endpoint for breaking wire changes. Keep the current endpoint
and serializer unchanged during a deprecation window, translate both versions
into the same domain request, and publish compatibility fixtures before routing
traffic to the new version.
