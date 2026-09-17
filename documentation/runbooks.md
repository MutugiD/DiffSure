# Operational Runbooks

## Install from source

Prerequisites are Python 3.12, `uv`, Git, Docker with Compose, and enough local
space for the multi-toolchain acceptance image.

```text
uv sync --locked --all-groups
docker build -t acceptance:latest acceptance
uv run diffsure doctor
```

`doctor` exits zero only when Git, the Docker daemon, the configured acceptance
image, and the selected provider are ready. Its JSON output contains no secret
values or host paths.

## Run with local Ollama

Start Ollama, pull the default model, and start DiffSure:

```text
docker compose -f compose.yml -f compose.ollama.yml --profile ollama up -d ollama
docker compose -f compose.yml -f compose.ollama.yml --profile ollama exec ollama ollama pull qwen3:8b
docker compose -f compose.yml -f compose.ollama.yml --profile ollama up -d --build diffsure
curl --fail http://127.0.0.1:8000/health
```

The acceptance image must exist in the same Docker daemon. On Linux, set
`DOCKER_GID` to the group ID that owns `/var/run/docker.sock` before Compose
starts the non-root service.

## Run with OpenAI

Keep the key outside files and shell history where the environment supports a
secret injection mechanism. OpenAI is selected explicitly and never used as a
fallback.

```text
DIFFSURE_PROVIDER=openai
DIFFSURE_MODEL=gpt-5.6-terra
OPENAI_API_KEY=<injected-secret>
docker compose up -d --build diffsure
curl --fail http://127.0.0.1:8000/health
```

Hosted requests set `store: false` and expose only local repository tools.

## Use a published image

```text
docker pull ghcr.io/mutugid/diffsure:edge
DIFFSURE_IMAGE=ghcr.io/mutugid/diffsure:edge docker compose up -d --no-build diffsure
```

Commit-SHA tags are immutable. `edge` follows protected `main`; `latest` is
published only for a `v*` release tag. Published images include OCI labels,
provenance, and an SBOM and pass a vulnerability scan before publication.

## Run the public harness

From the supplied public candidate directory, with the service healthy:

```text
python harness/run_client.py --url http://127.0.0.1:8000 tasks/public/* --local --concurrency 3 --out results/
```

Do not use reviewer-only tasks, reference patches, or private acceptance files.
Harness output belongs under `results/` and is not committed except for the
curated release report.

## Troubleshoot readiness

- `git=false`: install Git in the service environment.
- `docker=false`: verify the Docker daemon and socket permissions.
- `acceptance_image=false`: build or pull the configured acceptance image.
- `provider=false` with Ollama: verify the URL and that the model is pulled.
- `provider=false` with OpenAI: verify explicit provider selection and secret
  injection without printing the key.
- `capacity=false`: wait for an admitted solve to finish; readiness recovers
  automatically unless shutdown has begun.

Use `docker compose logs diffsure` for sanitized service diagnostics. Candidate
output is bounded and appears only in the requesting solve record.

## Control cost and load

Prefer Ollama for development. Set `DIFFSURE_CAPACITY` and
`DIFFSURE_PROVIDER_CAPACITY` to match host and provider limits, retain deadline
reserves, and monitor token, cost, null-result, cutoff, candidate, and repair
counters. Select OpenAI only for an intentional hosted run and apply external
account spend limits.
