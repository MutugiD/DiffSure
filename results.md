# Public Acceptance Results

Validation date: 2026-09-18

## Paid API benchmarking

The benchmark used hosted `gpt-5.5` through the authenticated Codex CLI subscription,
with `OPENAI_API_KEY` and `CODEX_API_KEY` removed. This avoids additional metered API
credits while exercising a paid OpenAI model. Generated diffs were graded with the
official public `harness/grade.py` in `acceptance:latest`.

The first lineage ran at concurrency three. Six patches passed. The token-bucket patch
passed static and apply validation but failed one behavioral acceptance case. A bounded
repair received the parent diff and observed failure, then passed the complete grader.

| Task | Selected attempt | Generation | Grade | Diff | Static/apply/tests |
|---|---:|---:|---:|---:|---|
| 01-pricing-tax | first | 98.80 s | 2.78 s | 333 B | pass/pass/pass |
| 02-slugify | first | 82.25 s | 2.88 s | 592 B | pass/pass/pass |
| 03-token-bucket | repair | 162.24 + 51.39 s | 2.64 + 1.83 s | 1,249 B | pass/pass/pass |
| 06-js-parse-duration | first | 78.26 s | 4.62 s | 1,204 B | pass/pass/pass |
| 07-bash-semver-bump | first | 84.35 s | 3.12 s | 1,062 B | pass/pass/pass |
| 08-go-ring-buffer | first | 52.80 s | 32.61 s | 1,234 B | pass/pass/pass |
| 11-c-str-trim | first | 158.91 s | 2.17 s | 638 B | pass/pass/pass |

Aggregate selected result:

- Acceptance: 7/7 (100%).
- Pre-execution rejection: 0/7.
- Missed deadlines: 0/7.
- Null diffs: 0/7.
- Concurrency: three.
- Selected provider/model: OpenAI through Codex subscription, `gpt-5.5`.
- Metered API cost: $0.00; subscription usage is not reported as an API dollar cost.

The initial token-bucket candidate and a second independent lineage both failed the
backward-time case. The bounded repair corrected the failure and was independently
accepted. Raw prompts, model logs, diffs, and grader logs remain in ignored local
`.release-results/codex-validation/` evidence.

## Local Ollama comparison

`qwen3:8b` completed 0/7 tasks in the earlier service-level run. All seven requests
failed closed with null diffs, with no missed deadline and no paid cost. Those failures
were provider throughput/errors rather than pre-execution diff rejections.
