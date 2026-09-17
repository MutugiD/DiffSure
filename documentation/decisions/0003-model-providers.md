# ADR-0003: Use Explicit Model Provider Selection

- Status: accepted
- Date: 2026-09-17

## Decision

Provide Ollama and OpenAI adapters behind one normalized protocol. Default to
local `qwen3:8b`; use `gpt-5.6-terra` only when OpenAI is explicitly selected.
Never fail over automatically to a paid provider.

## Consequences

Local operation has no token charge. Hosted runs can improve solve quality but
must report observed usage and require an out-of-band credential.
