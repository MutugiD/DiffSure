# Paid OpenAI Model Validation with Codex CLI

This runbook validates DiffSure's public patch outcomes with a hosted OpenAI model
through an authenticated Codex subscription. It is the assessment-safe replacement
for buying metered API credits. The model is hosted and paid-plan backed; only the
billing transport differs from direct Responses API execution.

The validation deliberately bypasses DiffSure's provider adapter. Existing contract,
HTTP concurrency, sandbox, and clean-delivery integration tests cover those paths.
This run proves model patch quality against the supplied official public grader.

## Boundaries

- Use only `Challenge2/candidate`, never reviewer files.
- Remove `OPENAI_API_KEY` and `CODEX_API_KEY` from each Codex subprocess.
- Give each session only a copied public task repository and its task text.
- Run with `--sandbox workspace-write`, no approval prompts, and an ephemeral session.
- Grade resulting diffs with `harness/grade.py` in `acceptance:latest`.
- Write raw evidence beneath ignored `.release-results/`; commit only `results.md`.

## Prerequisites

```powershell
codex --version
docker image inspect acceptance:latest
```

The installed CLI supports `gpt-5.5`. The current installed version requires an
upgrade before it can run `gpt-5.6-terra`, so the recorded assessment uses
`gpt-5.5` consistently.

## First lineage

Use a new output directory for every run:

```powershell
python tools/codex_public_validation.py `
  --candidate-root D:\clients-ops\proposals\ChallengeBox\Challenge2\candidate `
  --output .release-results\codex-gpt55-lineage1 `
  --model gpt-5.5 `
  --concurrency 3
```

The command exits zero only when every generated diff is accepted. A nonzero exit
with a valid `report.json` means one or more candidates were safely rejected.

## Bounded repair

When a candidate fails, place a concise observed failure summary in an ignored text
file. Seed a fresh repository with the rejected parent diff and run one repair:

```powershell
python tools/codex_public_validation.py `
  --candidate-root D:\clients-ops\proposals\ChallengeBox\Challenge2\candidate `
  --output .release-results\codex-gpt55-repair `
  --model gpt-5.5 `
  --concurrency 1 `
  --task 03-token-bucket `
  --repair-from .release-results\codex-gpt55-lineage1\03-token-bucket\candidate.diff `
  --failure-file .release-results\token-bucket-failure.txt
```

The repaired diff contains the complete parent-plus-repair patch and is independently
graded from a fresh snapshot. Select it only if it passes the official grader.

## Release interpretation

Combine accepted first-lineage candidates with accepted repairs. Record task outcome,
generation and grading duration, diff size, model, aggregate acceptance, null rate,
deadline rate, and billing mode in `results.md`. Do not claim direct API transport or
API token cost when the Codex subscription supplied the model execution.
